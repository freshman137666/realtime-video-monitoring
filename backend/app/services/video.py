import cv2
import numpy as np
import os
from flask import Response
from ultralytics import YOLO

from app.services.danger_zone import DANGER_ZONE
from app.services.detection import process_detection_results, get_model
from app.services.alerts import update_detection_time, reset_alerts

def video_feed():
    """实时视频流处理，包括目标检测和人脸识别"""
    # 重置警报，以便为新的实时会话提供干净的状态
    reset_alerts()

    # 初始化YOLO模型
    model = get_model()
    
    # 为本次实时会话创建一个新的人脸识别缓存
    face_recognition_cache = {}

    # 打开默认摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：无法打开摄像头。")
        return Response("无法打开摄像头。", mimetype='text/plain')

    frame_count = 0

    def generate():
        nonlocal frame_count
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # 计算帧之间的时间差以进行徘徊检测
            time_diff = update_detection_time()
            
            # 使用YOLOv8进行目标追踪
            # persist=True 告诉SDK当前图像或帧是序列的一部分
            results = model.track(frame, persist=True)
            
            # 我们不再使用plot()，而是自己绘制以避免双重边框
            processed_frame = frame.copy()
            
            # 在绘制的帧上应用我们的自定义检测逻辑
            # (危险区域、人脸识别、告警等)
            process_detection_results(results, processed_frame, time_diff, frame_count, face_recognition_cache)
            
            # 将处理后的帧编码为JPEG格式
            (flag, encodedImage) = cv2.imencode(".jpg", processed_frame)
            if not flag:
                continue
                
            # 以multipart格式产生输出帧
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                  bytearray(encodedImage) + b'\r\n')
            
    # 返回一个包含视频流的HTTP响应
    return Response(generate(),
                    mimetype = "multipart/x-mixed-replace; boundary=frame") 