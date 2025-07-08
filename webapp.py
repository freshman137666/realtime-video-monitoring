import argparse
import io
from PIL import Image
import datetime
import time
import math

import torch
import cv2
import numpy as np
import tensorflow as tf
from re import DEBUG, sub
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    send_file,
    url_for,
    Response,
    jsonify,
)
from werkzeug.utils import secure_filename, send_from_directory
import os
import subprocess
from subprocess import Popen
import re
import requests
import shutil
import glob
from collections import defaultdict


from ultralytics import YOLO


app = Flask(__name__)

# 定义全局变量
# 危险区域的多边形坐标 (x, y) 格式，这里先硬编码一个示例区域
# 在实际应用中，这应该是可以通过前端界面设置的
# 调整危险区域到道路上，覆盖车辆经过的位置
DANGER_ZONE = np.array([[100, 700], [600, 700], [600, 800], [100, 800]], np.int32)

# 安全距离阈值（像素）
SAFETY_DISTANCE = 100  # 进一步增加安全距离阈值

# 停留时间阈值（秒）
LOITERING_THRESHOLD = 2.0  # 降低阈值，更容易触发告警

# 需要检测的目标类别 (扩展到人和车辆)
TARGET_CLASSES = [0, 2, 7]  # person, car, truck

# 用于跟踪目标在危险区域内的停留时间
target_loitering_time = defaultdict(float)

# 上次检测的时间戳
last_detection_time = time.time()

# 用于存储告警信息
alerts = []

# 检查点是否在多边形内部
def point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# 计算点到多边形边缘的最小距离
def distance_to_polygon(point, polygon):
    min_distance = float('inf')
    x, y = point
    n = len(polygon)
    
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        
        # 计算点到线段的距离
        A = x - x1
        B = y - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        # 避免除以零
        if len_sq == 0:
            dist = math.sqrt(A * A + B * B)
        else:
            param = dot / len_sq
            
            if param < 0:
                xx = x1
                yy = y1
            elif param > 1:
                xx = x2
                yy = y2
            else:
                xx = x1 + param * C
                yy = y1 + param * D
                
            dist = math.sqrt((x - xx) ** 2 + (y - yy) ** 2)
            
        min_distance = min(min_distance, dist)
    
    return min_distance


@app.route("/")
def hello_world():
    # return render_template("index.html")
    if "image_path" in request.args:
        image_path = request.args["image_path"]
        return render_template("index.html", image_path=image_path)
    return render_template("index.html", alerts=alerts)  # 传递告警信息到模板

@app.route("/", methods=["GET", "POST"])
def predict_img():
    global alerts, target_loitering_time, last_detection_time  # 将全局变量声明移到函数开头
    
    if request.method == "POST":
        if 'file' in request.files:
            # 清空之前的告警
            alerts = []
            
            f = request.files['file']
            basepath = os.path.dirname(__file__)
            filepath = os.path.join(basepath, 'uploads', f.filename)
            print("upload folder is ", filepath)
            f.save(filepath)
            predict_img.imgpath = f.filename
            print("printing predict_img :::::: ", predict_img)

            file_extension = f.filename.rsplit('.', 1)[1].lower()

            if file_extension == 'jpg':
                # Handle image upload
                img = cv2.imread(filepath)

                # Perform the detection
                model = YOLO('yolov8n.pt')
                # 对于图片，我们仍然使用检测模式，因为追踪主要用于视频
                detections = model(img, save=True)

                # Find the latest subdirectory in the 'runs/detect' folder
                folder_path = os.path.join(basepath, 'runs', 'detect')
                subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
                latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))

                # Construct the relative path to the detected image file
                static_folder = os.path.join(basepath, 'static', 'assets')
                relative_image_path = os.path.relpath(os.path.join(folder_path, latest_subfolder, f.filename), static_folder)
                image_path = os.path.join(folder_path, latest_subfolder, f.filename)
                print("Relative image path:", relative_image_path)  # Print the relative_image_path for debugging
                
                return render_template('index.html', image_path=relative_image_path, media_type='image', alerts=alerts)

            elif file_extension == "mp4":
                # Handle video upload
                video_path = filepath  # replace with your video path
                cap = cv2.VideoCapture(video_path)

                # get video dimensions
                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                # Define the codec and create VideoWriter object
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(
                    "output.mp4", fourcc, 30.0, (frame_width, frame_height)
                )

                # initialize the YOLOv8 model here
                model = YOLO("yolov8n.pt")
                
                # 重置目标停留时间
                target_loitering_time = defaultdict(float)
                last_detection_time = time.time()
                alerts = []

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # 计算时间差
                    current_time = time.time()
                    time_diff = current_time - last_detection_time
                    last_detection_time = current_time

                    # 将检测模式改为追踪模式
                    results = model.track(frame, persist=True)  # persist=True 保持ID一致性
                    print(results)
                    cv2.waitKey(1)

                    # 获取处理后的帧（带有检测框的）
                    res_plotted = results[0].plot()
                    
                    # 绘制危险区域 - 使用半透明效果
                    overlay = res_plotted.copy()
                    danger_zone_pts = DANGER_ZONE.reshape((-1, 1, 2))
                    cv2.fillPoly(overlay, [danger_zone_pts], (0, 0, 255, 128))  # 红色填充，半透明
                    cv2.addWeighted(overlay, 0.4, res_plotted, 0.6, 0, res_plotted)  # 增加透明度到40%
                    cv2.polylines(res_plotted, [danger_zone_pts], True, (0, 0, 255), 3)  # 加粗边框
                    
                    # 在危险区域中添加文字
                    danger_zone_center = np.mean(DANGER_ZONE, axis=0, dtype=np.int32)
                    cv2.putText(res_plotted, "Danger Zone", 
                                (danger_zone_center[0] - 60, danger_zone_center[1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)  # 使用英文文字
                    
                    # 打印危险区域坐标，帮助调试
                    print(f"危险区域坐标: {DANGER_ZONE}, 安全距离阈值: {SAFETY_DISTANCE}px")

                    # 如果有追踪结果，在画面上显示追踪ID
                    if hasattr(results[0], 'boxes') and hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
                        boxes = results[0].boxes.xyxy.cpu().numpy()
                        ids = results[0].boxes.id.int().cpu().numpy()
                        classes = results[0].boxes.cls.cpu().numpy()
                        
                        # 获取类别名称
                        class_names = model.names
                        
                        # 打印检测到的所有物体，帮助调试
                        detected_objects = [class_names[int(cls)] for cls in classes]
                        print(f"检测到的物体: {detected_objects}")
                        print(f"危险区域坐标: {DANGER_ZONE}")
                        
                        for box, id, cls in zip(boxes, ids, classes):
                            x1, y1, x2, y2 = box
                            class_name = class_names[int(cls)]
                            
                            # 只处理指定类别的目标 (人、汽车、卡车)
                            if int(cls) in TARGET_CLASSES:
                                # 计算目标的底部中心点
                                foot_point = (int((x1 + x2) / 2), int(y2))
                                
                                # 打印目标位置，帮助调试
                                print(f"目标 {id} ({class_name}) 位置: {foot_point}")
                                
                                # 检查是否在危险区域内
                                in_danger_zone = point_in_polygon(foot_point, DANGER_ZONE)
                                
                                # 计算到危险区域的距离
                                distance = distance_to_polygon(foot_point, DANGER_ZONE)
                                print(f"目标 {id} 到危险区域距离: {distance:.1f}px, 在区域内: {in_danger_zone}")
                                
                                # 确定标签颜色和告警状态
                                label_color = (0, 255, 0)  # 默认绿色
                                alert_status = None
                                
                                # 如果在危险区域内，更新停留时间
                                if in_danger_zone:
                                    target_loitering_time[id] += time_diff
                                    print(f"目标 {id} 在危险区域内停留时间: {target_loitering_time[id]:.1f}s")
                                    
                                    # 如果停留时间超过阈值，标记为红色并记录告警
                                    if target_loitering_time[id] >= LOITERING_THRESHOLD:
                                        label_color = (0, 0, 255)  # 红色
                                        alert_status = f"ID:{id} ({class_name}) staying in danger zone for {target_loitering_time[id]:.1f}s"
                                        if alert_status not in alerts:
                                            alerts.append(alert_status)
                                            print(f"Alert: {alert_status}")
                                else:
                                    # 如果不在区域内，重置停留时间
                                    target_loitering_time[id] = 0
                                    
                                    # 如果距离小于安全距离，标记为黄色并记录告警
                                    if distance < SAFETY_DISTANCE:
                                        label_color = (0, 255, 255)  # 黄色
                                        alert_status = f"ID:{id} ({class_name}) too close to danger zone ({distance:.1f}px)"
                                        if alert_status not in alerts:
                                            alerts.append(alert_status)
                                            print(f"Alert: {alert_status}")
                                
                                # 在每个目标上方显示ID和类别
                                label = f"ID:{id} {class_name}"
                                if in_danger_zone:
                                    label += f" time:{target_loitering_time[id]:.1f}s"
                                elif distance < SAFETY_DISTANCE:
                                    label += f" dist:{distance:.1f}px"
                                    
                                cv2.putText(res_plotted, label, (int(x1), int(y1)-10), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, label_color, 2)
                                            
                                # 在目标底部位置画一个点
                                cv2.circle(res_plotted, foot_point, 5, label_color, -1)
                                
                                # 画一条从目标底部到危险区域最近点的线
                                if not in_danger_zone and distance < SAFETY_DISTANCE * 2:
                                    # 找到危险区域上最近的点
                                    min_dist = float('inf')
                                    closest_point = None
                                    for i in range(len(DANGER_ZONE)):
                                        p1 = DANGER_ZONE[i]
                                        p2 = DANGER_ZONE[(i + 1) % len(DANGER_ZONE)]
                                        
                                        # 计算点到线段的最近点
                                        line_vec = p2 - p1
                                        line_len = np.linalg.norm(line_vec)
                                        line_unitvec = line_vec / line_len
                                        
                                        pt_vec = np.array(foot_point) - p1
                                        proj_len = np.dot(pt_vec, line_unitvec)
                                        
                                        if proj_len < 0:
                                            closest_pt = p1
                                        elif proj_len > line_len:
                                            closest_pt = p2
                                        else:
                                            closest_pt = p1 + line_unitvec * proj_len
                                        
                                        d = np.linalg.norm(np.array(foot_point) - closest_pt)
                                        if d < min_dist:
                                            min_dist = d
                                            closest_point = tuple(map(int, closest_pt))
                                    
                                    # 画线
                                    if closest_point:
                                        cv2.line(res_plotted, foot_point, closest_point, label_color, 2)
                            else:
                                # 对于不在监控类别中的目标，仍然显示ID和类别，但使用默认绿色
                                label = f"ID:{id} {class_name}"
                                cv2.putText(res_plotted, label, (int(x1), int(y1)-10), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                    cv2.imshow("result", res_plotted)

                    # write the frame to the output video
                    out.write(res_plotted)

                    if cv2.waitKey(1) == ord("q"):
                        break

                return render_template('index.html', video_path='output.mp4', media_type='video', alerts=alerts)

    # If no file uploaded or GET request, return the template with default values
    return render_template("index.html", image_path="", media_type='image', alerts=alerts)



@app.route("/<path:filename>")
def display(filename):
    folder_path = "runs/detect"
    subfolders = [
        f
        for f in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, f))
    ]
    latest_subfolder = max(
        subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x))
    )
    directory = os.path.join(folder_path, latest_subfolder)
    print("printing directory: ", directory)
    files = os.listdir(directory)
    latest_file = files[0]

    print(latest_file)

    image_path = os.path.join(directory, latest_file)

    file_extension = latest_file.rsplit(".", 1)[1].lower()

    if file_extension == "jpg":
        return send_file(image_path, mimetype="image/jpeg")
    elif file_extension == "mp4":
        return send_file(image_path, mimetype="video/mp4")
    else:
        return "Invalid file format"


def get_frame():
    folder_path = os.getcwd()
    mp4_files = "output.mp4"
    print("files being read...")
    video = cv2.VideoCapture(mp4_files)  # detected video path
    while True:
        success, frame = video.read()
        if not success:
            print("file not being read")
            break
        else:
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n"
        )
        time.sleep(0.1)  # Control the frame rate to display one frame every 100 milliseconds:



# function to display the detected objects video on html page
@app.route("/video_feed")
def video_feed():
    # folder_path = os.getcwd()
    # mp4_file = "output.mp4"
    # video_path = os.path.join(folder_path, mp4_file)
    # return send_file(video_path, mimetype="video")
    return Response(get_frame(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/webcam_feed")
def webcam_feed():
    global target_loitering_time, last_detection_time, alerts  # 确保在使用前声明全局变量
    
    cap = cv2.VideoCapture(0) # 0 for camera
    
    # 重置目标停留时间
    target_loitering_time = defaultdict(float)
    last_detection_time = time.time()
    alerts = []

    def generate():
        global target_loitering_time, last_detection_time  # 在内部函数中也声明全局变量
        
        # 初始化YOLO模型
        model = YOLO("yolov8n.pt")
        
        while True:
            success, frame = cap.read()
            if not success:
                break

            # 计算时间差
            current_time = time.time()
            time_diff = current_time - last_detection_time
            last_detection_time = current_time

            # 使用追踪模式而不是检测模式
            results = model.track(frame, persist=True)  # persist=True 保持ID一致性

            # 获取处理后的帧（带有检测框的）
            res_plotted = results[0].plot()
            
            # 绘制危险区域 - 使用半透明效果
            overlay = res_plotted.copy()
            danger_zone_pts = DANGER_ZONE.reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [danger_zone_pts], (0, 0, 255))  # 红色填充
            cv2.addWeighted(overlay, 0.4, res_plotted, 0.6, 0, res_plotted)  # 增加透明度到40%
            cv2.polylines(res_plotted, [danger_zone_pts], True, (0, 0, 255), 3)  # 加粗边框
            
            # 在危险区域中添加文字
            danger_zone_center = np.mean(DANGER_ZONE, axis=0, dtype=np.int32)
            cv2.putText(res_plotted, "Danger Zone", 
                        (danger_zone_center[0] - 60, danger_zone_center[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)  # 使用英文文字

            # 如果有追踪结果，在画面上显示追踪ID
            if hasattr(results[0], 'boxes') and hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                ids = results[0].boxes.id.int().cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy()
                
                # 获取类别名称
                class_names = model.names
                
                # 打印检测到的所有物体，帮助调试
                detected_objects = [class_names[int(cls)] for cls in classes]
                print(f"检测到的物体: {detected_objects}")
                
                for box, id, cls in zip(boxes, ids, classes):
                    x1, y1, x2, y2 = box
                    class_name = class_names[int(cls)]
                    
                    # 只处理指定类别的目标 (人、汽车、卡车)
                    if int(cls) in TARGET_CLASSES:
                        # 计算目标的底部中心点
                        foot_point = (int((x1 + x2) / 2), int(y2))
                        
                        # 检查是否在危险区域内
                        in_danger_zone = point_in_polygon(foot_point, DANGER_ZONE)
                        
                        # 计算到危险区域的距离
                        distance = distance_to_polygon(foot_point, DANGER_ZONE)
                        
                        # 确定标签颜色和告警状态
                        label_color = (0, 255, 0)  # 默认绿色
                        alert_status = None
                        
                        # 如果在危险区域内，更新停留时间
                        if in_danger_zone:
                            target_loitering_time[id] += time_diff
                            
                            # 如果停留时间超过阈值，标记为红色并记录告警
                            if target_loitering_time[id] >= LOITERING_THRESHOLD:
                                label_color = (0, 0, 255)  # 红色
                                alert_status = f"ID:{id} ({class_name}) staying in danger zone for {target_loitering_time[id]:.1f}s"
                                if alert_status not in alerts:
                                    alerts.append(alert_status)
                                    print(f"Alert: {alert_status}")
                        else:
                            # 如果不在区域内，重置停留时间
                            target_loitering_time[id] = 0
                            
                            # 如果距离小于安全距离，标记为黄色并记录告警
                            if distance < SAFETY_DISTANCE:
                                label_color = (0, 255, 255)  # 黄色
                                alert_status = f"ID:{id} ({class_name}) too close to danger zone ({distance:.1f}px)"
                                if alert_status not in alerts:
                                    alerts.append(alert_status)
                                    print(f"Alert: {alert_status}")
                        
                        # 在每个目标上方显示ID和类别
                        label = f"ID:{id} {class_name}"
                        if in_danger_zone:
                            label += f" time:{target_loitering_time[id]:.1f}s"
                        elif distance < SAFETY_DISTANCE:
                            label += f" dist:{distance:.1f}px"
                            
                        cv2.putText(res_plotted, label, (int(x1), int(y1)-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, label_color, 2)
                                    
                        # 在目标底部位置画一个点
                        cv2.circle(res_plotted, foot_point, 5, label_color, -1)
                        
                        # 画一条从目标底部到危险区域最近点的线
                        if not in_danger_zone and distance < SAFETY_DISTANCE * 2:
                            # 找到危险区域上最近的点
                            min_dist = float('inf')
                            closest_point = None
                            for i in range(len(DANGER_ZONE)):
                                p1 = DANGER_ZONE[i]
                                p2 = DANGER_ZONE[(i + 1) % len(DANGER_ZONE)]
                                
                                # 计算点到线段的最近点
                                line_vec = p2 - p1
                                line_len = np.linalg.norm(line_vec)
                                line_unitvec = line_vec / line_len
                                
                                pt_vec = np.array(foot_point) - p1
                                proj_len = np.dot(pt_vec, line_unitvec)
                                
                                if proj_len < 0:
                                    closest_pt = p1
                                elif proj_len > line_len:
                                    closest_pt = p2
                                else:
                                    closest_pt = p1 + line_unitvec * proj_len
                                
                                d = np.linalg.norm(np.array(foot_point) - closest_pt)
                                if d < min_dist:
                                    min_dist = d
                                    closest_point = tuple(map(int, closest_pt))
                            
                            # 画线
                            if closest_point:
                                cv2.line(res_plotted, foot_point, closest_point, label_color, 2)
                        else:
                            # 对于不在监控类别中的目标，仍然显示ID和类别，但使用默认绿色
                            label = f"ID:{id} {class_name}"
                            cv2.putText(res_plotted, label, (int(x1), int(y1)-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # 转换为JPEG格式用于流式传输
            ret, buffer = cv2.imencode(".jpg", res_plotted)
            frame = buffer.tobytes()

            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n"
            )

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


# 添加一个新路由，用于获取最新的告警信息
@app.route("/get_alerts")
def get_alerts():
    return jsonify({"alerts": alerts})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing yolov8 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    model = YOLO("yolov8n.pt")
    app.run(host="0.0.0.0", port=args.port, debug=True)
