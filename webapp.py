import argparse
import io
from PIL import Image
import datetime
import time
import math
import json

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

# 配置文件路径
CONFIG_FILE = 'danger_zone_config.json'

# 加载危险区域配置
def load_danger_zone_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                danger_zone = np.array(config['danger_zone'], np.int32)
                safety_distance = config.get('safety_distance', 100)
                loitering_threshold = config.get('loitering_threshold', 2.0)
                return danger_zone, safety_distance, loitering_threshold
        except Exception as e:
            print(f"Error loading config: {e}")
    return np.array([[100, 700], [600, 700], [600, 800], [100, 800]], np.int32), 100, 2.0  # 默认值

# 保存危险区域配置
def save_danger_zone_config(danger_zone, safety_distance, loitering_threshold):
    try:
        with open(CONFIG_FILE, 'w') as f:
            config = {
                'danger_zone': danger_zone.tolist(),
                'safety_distance': safety_distance,
                'loitering_threshold': loitering_threshold
            }
            json.dump(config, f)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# 定义全局变量
# 危险区域的多边形坐标 (x, y) 格式
DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD = load_danger_zone_config()

# 安全距离阈值（像素）
# SAFETY_DISTANCE = 100  # 进一步增加安全距离阈值

# 停留时间阈值（秒）
# LOITERING_THRESHOLD = 2.0  # 降低阈值，更容易触发告警

# 需要检测的目标类别 (扩展到人和车辆)
TARGET_CLASSES = [0, 2, 7]  # person, car, truck

# 用于跟踪目标在危险区域内的停留时间
target_loitering_time = defaultdict(float)

# 上次检测的时间戳
last_detection_time = time.time()

# 用于存储告警信息
alerts = []

# 危险区域编辑模式标志
edit_mode = False

# 当前正在编辑的点索引
current_point_index = -1

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
                                        # 使用纯红色
                                        label_color = (0, 0, 255)  # BGR格式：红色
                                        alert_status = f"ID:{id} ({class_name}) staying in danger zone for {target_loitering_time[id]:.1f}s"
                                        if alert_status not in alerts:
                                            alerts.append(alert_status)
                                            print(f"Alert: {alert_status}")
                                    else:
                                        # 根据停留时间从橙色到红色渐变
                                        ratio = min(1.0, target_loitering_time[id] / LOITERING_THRESHOLD)
                                        # 从橙色(0,165,255)到红色(0,0,255)
                                        label_color = (0, int(165 * (1 - ratio)), 255)
                                else:
                                    # 如果不在区域内，重置停留时间
                                    target_loitering_time[id] = 0
                                    
                                    # 如果距离小于安全距离，根据距离设置颜色从绿色到黄色
                                    if distance < SAFETY_DISTANCE:
                                        # 计算距离比例
                                        ratio = distance / SAFETY_DISTANCE
                                        # 从黄色(0,255,255)到绿色(0,255,0)渐变
                                        label_color = (0, 255, int(255 * (1 - ratio)))
                                        
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
                                    
                                # 根据危险程度调整边框粗细
                                thickness = 2  # 默认粗细
                                if in_danger_zone:
                                    # 在危险区域内，根据停留时间增加边框粗细
                                    thickness = max(2, int(4 * min(1.0, target_loitering_time[id] / LOITERING_THRESHOLD)))
                                    
                                    # 如果停留时间超过阈值，添加警告标记
                                    if target_loitering_time[id] >= LOITERING_THRESHOLD:
                                        # 在目标上方绘制警告三角形
                                        triangle_height = 20
                                        triangle_base = 20
                                        triangle_center_x = int((x1 + x2) / 2)
                                        triangle_top_y = int(y1) - 25
                                        
                                        triangle_pts = np.array([
                                            [triangle_center_x - triangle_base//2, triangle_top_y + triangle_height],
                                            [triangle_center_x + triangle_base//2, triangle_top_y + triangle_height],
                                            [triangle_center_x, triangle_top_y]
                                        ], np.int32)
                                        
                                        cv2.fillPoly(res_plotted, [triangle_pts], (0, 0, 255))  # 红色填充
                                        cv2.polylines(res_plotted, [triangle_pts], True, (0, 0, 0), 1)  # 黑色边框
                                        
                                        # 在三角形中绘制感叹号
                                        cv2.putText(res_plotted, "!", 
                                                    (triangle_center_x - 3, triangle_top_y + triangle_height - 5), 
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                                elif distance < SAFETY_DISTANCE:
                                    # 不在危险区域但接近时，根据距离增加边框粗细
                                    thickness = max(1, int(3 * (1 - distance / SAFETY_DISTANCE)))
                                
                                # 绘制边框
                                cv2.rectangle(res_plotted, (int(x1), int(y1)), (int(x2), int(y2)), label_color, thickness)
                                
                                # 绘制标签
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
    global target_loitering_time, last_detection_time, alerts, edit_mode, DANGER_ZONE, current_point_index  # 确保在使用前声明全局变量
    
    cap = cv2.VideoCapture(0) # 0 for camera
    
    # 重置目标停留时间
    target_loitering_time = defaultdict(float)
    last_detection_time = time.time()
    alerts = []
    
    # 鼠标事件处理函数
    def handle_mouse_event(event, x, y, flags, param):
        global DANGER_ZONE, current_point_index, edit_mode
        
        if not edit_mode:
            return
            
        if event == cv2.EVENT_LBUTTONDOWN:
            # 检查是否点击了现有点
            for i, point in enumerate(DANGER_ZONE):
                if np.linalg.norm(np.array([x, y]) - point) < 10:  # 10像素范围内
                    current_point_index = i
                    break
            else:
                # 如果没有点击现有点，添加新点
                DANGER_ZONE = np.append(DANGER_ZONE, [[x, y]], axis=0)
                current_point_index = len(DANGER_ZONE) - 1
                
        elif event == cv2.EVENT_MOUSEMOVE:
            # 如果正在拖动点，更新其位置
            if current_point_index != -1:
                DANGER_ZONE[current_point_index] = [x, y]
                
        elif event == cv2.EVENT_LBUTTONUP:
            # 释放鼠标，结束拖动
            current_point_index = -1
            
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右键删除最近的点
            for i, point in enumerate(DANGER_ZONE):
                if np.linalg.norm(np.array([x, y]) - point) < 10:  # 10像素范围内
                    DANGER_ZONE = np.delete(DANGER_ZONE, i, axis=0)
                    break

    def generate():
        global target_loitering_time, last_detection_time, DANGER_ZONE, edit_mode  # 在内部函数中也声明全局变量
        
        # 创建命名窗口并设置鼠标回调
        cv2.namedWindow("Video Feed")
        cv2.setMouseCallback("Video Feed", handle_mouse_event)
        
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

            # 保存原始帧的副本用于编辑模式
            original_frame = frame.copy()
            
            # 如果不在编辑模式，则进行正常的目标检测和追踪
            if not edit_mode:
                # 使用追踪模式而不是检测模式
                results = model.track(frame, persist=True)  # persist=True 保持ID一致性

                # 获取处理后的帧（带有检测框的）
                res_plotted = results[0].plot()
            else:
                # 在编辑模式下，使用原始帧
                res_plotted = original_frame
            
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
            
            # 在编辑模式下，为每个点添加标记和索引
            if edit_mode:
                for i, point in enumerate(DANGER_ZONE):
                    cv2.circle(res_plotted, tuple(point), 5, (0, 255, 255), -1)  # 黄色实心圆
                    cv2.putText(res_plotted, str(i), (point[0]+5, point[1]+5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # 添加编辑模式指示
                cv2.putText(res_plotted, "EDIT MODE - Click and drag points, right click to delete", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # 如果不在编辑模式，且有追踪结果，在画面上显示追踪ID
            if not edit_mode and hasattr(results[0], 'boxes') and hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
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
                                # 使用纯红色
                                label_color = (0, 0, 255)  # BGR格式：红色
                                alert_status = f"ID:{id} ({class_name}) staying in danger zone for {target_loitering_time[id]:.1f}s"
                                if alert_status not in alerts:
                                    alerts.append(alert_status)
                                    print(f"Alert: {alert_status}")
                            else:
                                # 根据停留时间从橙色到红色渐变
                                ratio = min(1.0, target_loitering_time[id] / LOITERING_THRESHOLD)
                                # 从橙色(0,165,255)到红色(0,0,255)
                                label_color = (0, int(165 * (1 - ratio)), 255)
                        else:
                            # 如果不在区域内，重置停留时间
                            target_loitering_time[id] = 0
                            
                            # 如果距离小于安全距离，根据距离设置颜色从绿色到黄色
                            if distance < SAFETY_DISTANCE:
                                # 计算距离比例
                                ratio = distance / SAFETY_DISTANCE
                                # 从黄色(0,255,255)到绿色(0,255,0)渐变
                                label_color = (0, 255, int(255 * (1 - ratio)))
                                
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
                            
                        # 根据危险程度调整边框粗细
                        thickness = 2  # 默认粗细
                        if in_danger_zone:
                            # 在危险区域内，根据停留时间增加边框粗细
                            thickness = max(2, int(4 * min(1.0, target_loitering_time[id] / LOITERING_THRESHOLD)))
                            
                            # 如果停留时间超过阈值，添加警告标记
                            if target_loitering_time[id] >= LOITERING_THRESHOLD:
                                # 在目标上方绘制警告三角形
                                triangle_height = 20
                                triangle_base = 20
                                triangle_center_x = int((x1 + x2) / 2)
                                triangle_top_y = int(y1) - 25
                                
                                triangle_pts = np.array([
                                    [triangle_center_x - triangle_base//2, triangle_top_y + triangle_height],
                                    [triangle_center_x + triangle_base//2, triangle_top_y + triangle_height],
                                    [triangle_center_x, triangle_top_y]
                                ], np.int32)
                                
                                cv2.fillPoly(res_plotted, [triangle_pts], (0, 0, 255))  # 红色填充
                                cv2.polylines(res_plotted, [triangle_pts], True, (0, 0, 0), 1)  # 黑色边框
                                
                                # 在三角形中绘制感叹号
                                cv2.putText(res_plotted, "!", 
                                            (triangle_center_x - 3, triangle_top_y + triangle_height - 5), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        elif distance < SAFETY_DISTANCE:
                            # 不在危险区域但接近时，根据距离增加边框粗细
                            thickness = max(1, int(3 * (1 - distance / SAFETY_DISTANCE)))
                        
                        # 绘制边框
                        cv2.rectangle(res_plotted, (int(x1), int(y1)), (int(x2), int(y2)), label_color, thickness)
                        
                        # 绘制标签
                        cv2.putText(res_plotted, label, (int(x1), int(y1)-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, label_color, 2)
                                    
                        # 在目标底部位置画一个点
                        foot_point = (int((x1 + x2) / 2), int(y2))
                        cv2.circle(res_plotted, foot_point, 5, label_color, -1)
                        
                        # 如果不在危险区域内但距离小于安全距离的2倍，绘制到危险区域的连接线
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
                            
                            # 绘制从目标到危险区域的连接线，颜色根据距离变化
                            if closest_point:
                                # 根据距离调整线条粗细和样式
                                line_thickness = max(1, int(3 * (1 - distance / (SAFETY_DISTANCE * 2))))
                                
                                # 绘制主线
                                cv2.line(res_plotted, foot_point, closest_point, label_color, line_thickness)
                                
                                # 在线上显示距离数字
                                mid_point = ((foot_point[0] + closest_point[0]) // 2, 
                                            (foot_point[1] + closest_point[1]) // 2)
                                cv2.putText(res_plotted, f"{distance:.1f}px", 
                                            (mid_point[0] + 5, mid_point[1] - 5),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, label_color, 1)
                                
                                # 如果距离小于安全距离，添加虚线效果
                                if distance < SAFETY_DISTANCE:
                                    # 计算线段长度
                                    line_length = np.linalg.norm(np.array(foot_point) - np.array(closest_point))
                                    # 计算单位向量
                                    if line_length > 0:
                                        unit_vector = (np.array(closest_point) - np.array(foot_point)) / line_length
                                        # 绘制短线段形成虚线效果
                                        for i in range(0, int(line_length), 10):
                                            start_point = np.array(foot_point) + i * unit_vector
                                            end_point = start_point + 5 * unit_vector
                                            start_point = tuple(map(int, start_point))
                                            end_point = tuple(map(int, end_point))
                                            cv2.line(res_plotted, start_point, end_point, (0, 0, 255), line_thickness + 1)
                        # 删除多余的else分支
                        # else:
                        #     # 对于不在监控类别中的目标，仍然显示ID和类别，但使用默认绿色
                        #     label = f"ID:{id} {class_name}"
                        #     cv2.putText(res_plotted, label, (int(x1), int(y1)-10), 
                        #                 cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # 显示处理后的帧
            cv2.imshow("Video Feed", res_plotted)
            if cv2.waitKey(1) & 0xFF == ord('e'):  # 按'e'键切换编辑模式
                edit_mode = not edit_mode
                print(f"Edit mode: {'ON' if edit_mode else 'OFF'}")

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

# 添加一个新路由，用于获取当前危险区域坐标
@app.route("/get_danger_zone")
def get_danger_zone():
    global DANGER_ZONE
    # 将NumPy数组转换为普通列表以便JSON序列化
    zone_list = DANGER_ZONE.tolist()
    return jsonify({"danger_zone": zone_list})

# 添加一个新路由，用于获取当前配置
@app.route("/get_config")
def get_config():
    global DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD
    return jsonify({
        "danger_zone": DANGER_ZONE.tolist(),
        "safety_distance": SAFETY_DISTANCE,
        "loitering_threshold": LOITERING_THRESHOLD
    })

# 添加一个新路由，用于更新危险区域坐标
@app.route("/update_danger_zone", methods=["POST"])
def update_danger_zone():
    global DANGER_ZONE
    data = request.json
    new_zone = data.get('danger_zone')
    
    if new_zone and len(new_zone) >= 3:  # 确保至少有3个点形成多边形
        DANGER_ZONE = np.array(new_zone, np.int32)
        # 保存到配置文件
        if save_danger_zone_config(DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD):
            return jsonify({"status": "success", "message": "Danger zone updated and saved successfully"})
        else:
            return jsonify({"status": "warning", "message": "Danger zone updated but failed to save to file"})
    else:
        return jsonify({"status": "error", "message": "Invalid danger zone coordinates"}), 400

# 添加一个新路由，用于更新安全距离和停留时间阈值
@app.route("/update_thresholds", methods=["POST"])
def update_thresholds():
    global SAFETY_DISTANCE, LOITERING_THRESHOLD
    data = request.json
    
    safety_distance = data.get('safety_distance')
    loitering_threshold = data.get('loitering_threshold')
    
    if safety_distance is not None:
        try:
            SAFETY_DISTANCE = int(safety_distance)
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid safety distance value"}), 400
            
    if loitering_threshold is not None:
        try:
            LOITERING_THRESHOLD = float(loitering_threshold)
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid loitering threshold value"}), 400
    
    # 保存到配置文件
    if save_danger_zone_config(DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD):
        return jsonify({
            "status": "success", 
            "message": "Thresholds updated and saved successfully",
            "safety_distance": SAFETY_DISTANCE,
            "loitering_threshold": LOITERING_THRESHOLD
        })
    else:
        return jsonify({
            "status": "warning", 
            "message": "Thresholds updated but failed to save to file",
            "safety_distance": SAFETY_DISTANCE,
            "loitering_threshold": LOITERING_THRESHOLD
        })

# 添加一个新路由，用于切换危险区域编辑模式
@app.route("/toggle_edit_mode", methods=["POST"])
def toggle_edit_mode():
    global edit_mode
    data = request.json
    edit_mode = data.get('edit_mode', False)
    return jsonify({"status": "success", "edit_mode": edit_mode})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing yolov8 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    model = YOLO("yolov8n.pt")
    app.run(host="0.0.0.0", port=args.port, debug=True)
