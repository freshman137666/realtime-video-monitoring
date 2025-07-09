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
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import os
import re
import shutil
import glob
from collections import defaultdict
from werkzeug.utils import secure_filename, send_from_directory

from ultralytics import YOLO

# 解决 "OMP: Error #15" 警告
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 定义上传目录路径
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)
print(f"上传目录: {UPLOADS_DIR}")

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

# API路由
@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "message": "Video monitoring API is operational"
    })

# API获取配置信息
@app.route("/api/config", methods=["GET"])
def get_config():
    global DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD
    return jsonify({
        "danger_zone": DANGER_ZONE.tolist(),
        "safety_distance": SAFETY_DISTANCE,
        "loitering_threshold": LOITERING_THRESHOLD
    })

# API更新危险区域坐标
@app.route("/api/update_danger_zone", methods=["POST"])
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

# API更新安全距离和停留时间阈值
@app.route("/api/update_thresholds", methods=["POST"])
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

# API切换危险区域编辑模式
@app.route("/api/toggle_edit_mode", methods=["POST"])
def toggle_edit_mode():
    global edit_mode
    data = request.json
    edit_mode = data.get('edit_mode', False)
    return jsonify({"status": "success", "edit_mode": edit_mode})

# API获取告警信息
@app.route("/api/alerts")
def get_alerts():
    return jsonify({"alerts": alerts})

# API上传文件处理
@app.route('/api/upload', methods=['POST'])
def upload_file():
    global alerts, target_loitering_time, last_detection_time
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    if file:
        # 清空之前的告警
        alerts = []
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOADS_DIR, filename)
        file.save(filepath)
        
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_extension == 'jpg':
            # 处理图片上传
            return process_image(filepath)
        elif file_extension == 'mp4':
            # 处理视频上传
            return process_video(filepath)
        else:
            return jsonify({
                "status": "error", 
                "message": "Unsupported file type. Please upload JPG or MP4."
            }), 400

def process_image(filepath):
    # 读取图片
    img = cv2.imread(filepath)
    if img is None:
        return jsonify({"status": "error", "message": "Failed to load image"}), 500
    
    # 执行对象检测
    model = YOLO('yolov8n.pt')
    detections = model(img)
    
    # 处理检测结果
    res_plotted = detections[0].plot()
    
    # 绘制危险区域
    danger_zone_pts = DANGER_ZONE.reshape((-1, 1, 2))
    overlay = res_plotted.copy()
    cv2.fillPoly(overlay, [danger_zone_pts], (0, 0, 255))
    cv2.addWeighted(overlay, 0.4, res_plotted, 0.6, 0, res_plotted)
    cv2.polylines(res_plotted, [danger_zone_pts], True, (0, 0, 255), 3)
    
    # 保存处理后的图像
    output_filename = 'processed_' + os.path.basename(filepath)
    output_path = os.path.join(UPLOADS_DIR, output_filename)
    print(f"保存处理后的图像到: {output_path}")
    cv2.imwrite(output_path, res_plotted)
    
    # 使用相对URL路径
    output_url = f"/api/files/{output_filename}"
    print(f"图像处理完成，输出URL: {output_url}")
    
    return jsonify({
        "status": "success",
        "media_type": "image",
        "file_url": output_url,
        "alerts": alerts
    })

def process_video(filepath):
    global alerts, target_loitering_time, last_detection_time
    
    # 创建输出视频路径
    output_filename = 'processed_' + os.path.basename(filepath)
    output_path = os.path.join(UPLOADS_DIR, output_filename)
    print(f"处理视频: {filepath}")
    print(f"输出路径: {output_path}")
    
    # 打开视频
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return jsonify({"status": "error", "message": "Failed to open video"}), 500
    
    # 获取视频属性
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # 初始化YOLOv8模型
    model = YOLO("yolov8n.pt")
    
    # 重置目标停留时间
    target_loitering_time = defaultdict(float)
    last_detection_time = time.time()
    alerts = []
    
    # 处理视频帧
    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"开始处理视频，总帧数: {total_frames}")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        if frame_count % 10 == 0:  # 每10帧打印一次进度
            progress = (frame_count / total_frames) * 100
            print(f"处理视频: {progress:.1f}% 完成")
        
        # 计算时间差
        current_time = time.time()
        time_diff = current_time - last_detection_time
        last_detection_time = current_time
        
        # 执行目标追踪
        results = model.track(frame, persist=True)
        
        # 获取处理后的帧
        res_plotted = results[0].plot()
        
        # 绘制危险区域
        overlay = res_plotted.copy()
        danger_zone_pts = DANGER_ZONE.reshape((-1, 1, 2))
        cv2.fillPoly(overlay, [danger_zone_pts], (0, 0, 255))
        cv2.addWeighted(overlay, 0.4, res_plotted, 0.6, 0, res_plotted)
        cv2.polylines(res_plotted, [danger_zone_pts], True, (0, 0, 255), 3)
        
        # 在危险区域中添加文字
        danger_zone_center = np.mean(DANGER_ZONE, axis=0, dtype=np.int32)
        cv2.putText(res_plotted, "Danger Zone", 
                    (danger_zone_center[0] - 60, danger_zone_center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        # 如果有追踪结果，在画面上显示追踪ID和危险区域告警
        if hasattr(results[0], 'boxes') and hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.int().cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy()
            
            # 获取类别名称
            class_names = model.names
            
            for box, id, cls in zip(boxes, ids, classes):
                x1, y1, x2, y2 = box
                class_name = class_names[int(cls)]
                
                # 只处理指定类别的目标
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
        
        # 写入处理后的帧到输出视频
        out.write(res_plotted)
    
    # 释放资源
    cap.release()
    out.release()
    
    # 使用相对URL路径
    output_url = f"/api/files/{output_filename}"
    print(f"视频处理完成，输出URL: {output_url}")
    
    return jsonify({
        "status": "success",
        "media_type": "video",
        "file_url": output_url,
        "alerts": alerts
    })

# API视频流
@app.route('/api/video_feed')
def video_feed():
    # 添加跨域头，以便前端可以加载视频流
    def generate():
        CAMERA_INDEX = 0  # 摄像头索引，可以根据实际情况修改
        MODEL_PATH = "yolov8n.pt"

        # --- 健壮性检查 1: 检查模型文件是否存在 ---
        if not os.path.exists(MODEL_PATH):
            error_msg = f"错误: YOLO 模型文件未在路径 {MODEL_PATH} 找到。"
            print(error_msg)
            # 创建一个包含错误消息的黑色图像
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, error_msg, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            ret, buffer = cv2.imencode(".jpg", error_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            return

        # --- 健壮性检查 2: 检查摄像头是否能打开 ---
        # 强制使用 CAP_DSHOW 以提高在Windows上的兼容性
        print(f"正在尝试使用 DSHOW 模式打开摄像头索引: {CAMERA_INDEX}...")
        cap = cv2.VideoCapture(CAMERA_INDEX + cv2.CAP_DSHOW)
        if not cap.isOpened():
            error_msg = f"错误: 无法打开摄像头索引 {CAMERA_INDEX}。"
            print(error_msg)
            # 创建一个包含错误消息的黑色图像
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, error_msg, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            ret, buffer = cv2.imencode(".jpg", error_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            return # 退出生成器

        # 初始化YOLO模型
        print("正在加载YOLO模型...")
        model = YOLO(MODEL_PATH)
        print("YOLO模型加载成功。")
        
        while True:
            success, frame = cap.read()
            if not success:
                print("无法从摄像头读取帧，视频流结束。")
                break
                
            # 执行目标追踪
            results = model.track(frame, persist=True)
            
            # 获取处理后的帧
            res_plotted = results[0].plot()
            
            # 绘制危险区域
            overlay = res_plotted.copy()
            danger_zone_pts = DANGER_ZONE.reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [danger_zone_pts], (0, 0, 255))
            cv2.addWeighted(overlay, 0.4, res_plotted, 0.6, 0, res_plotted)
            cv2.polylines(res_plotted, [danger_zone_pts], True, (0, 0, 255), 3)
            
            # 在危险区域中添加文字
            danger_zone_center = np.mean(DANGER_ZONE, axis=0, dtype=np.int32)
            cv2.putText(res_plotted, "Danger Zone", 
                        (danger_zone_center[0] - 60, danger_zone_center[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            
            # 转换为JPEG格式用于流式传输
            ret, buffer = cv2.imencode(".jpg", res_plotted)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                   
        # --- 健壮性检查 3: 确保在循环结束后释放摄像头 ---
        print("释放摄像头资源。")
        cap.release()
                   
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# API访问文件
@app.route('/api/files/<filename>')
def serve_file(filename):
    print(f"请求访问文件: {filename}, 目录: {UPLOADS_DIR}")
    # 确保安全的文件名访问
    filename = secure_filename(filename)
    return send_from_directory(UPLOADS_DIR, filename)

if __name__ == "__main__":
    # 解决 "OMP: Error #15" 警告
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    parser = argparse.ArgumentParser(description="Flask API exposing YOLOv8 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    parser.add_argument("--host", default="0.0.0.0", help="host address")
    args = parser.parse_args()
    
    # 初始化YOLO模型
    model = YOLO("yolov8n.pt")
    
    print(f"API server starting on http://{args.host}:{args.port}")
    # 禁用自动重载 (use_reloader=False) 来防止服务因文件变化而意外重启
    app.run(host=args.host, port=args.port, debug=True, use_reloader=False)
