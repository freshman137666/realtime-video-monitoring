import cv2
import numpy as np
import os
import time
from flask import Response
from ultralytics import YOLO

from app.services import detection as detection_service
from app.services.danger_zone import DANGER_ZONE
from app.services.alerts import update_detection_time, reset_alerts
from app.services import system_state

# 全局变量，用于控制摄像头视频流的循环
CAMERA_ACTIVE = False
# -- REMOVED --: Global model instances are removed to prevent state conflicts.
# model = None
# face_recognition_cache = {}

def video_feed():
    """实时视频流处理，为每个会话创建独立的模型实例。"""
    global CAMERA_ACTIVE
    CAMERA_ACTIVE = True

    # 重置警报，以便为新的实时会话提供干净的状态
    reset_alerts()

    # --- FIX: Create session-local model instances ---
    # These instances live only for the duration of this camera session.
    print("Initializing new model instances for real-time stream...")
    object_model_stream = YOLO(detection_service.OBJECT_MODEL_PATH)
    face_model_stream = YOLO(detection_service.FACE_MODEL_PATH)
    pose_model_stream = YOLO(detection_service.POSE_MODEL_PATH)
    smoking_model_service = detection_service.get_smoking_model() # This is a stateless service wrapper
    face_recognition_cache = {} # Create a fresh cache for this session

    # 打开默认摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：无法打开摄像头。")
        return Response("无法打开摄像头。", mimetype='text/plain')

    frame_count = 0

    def generate():
        nonlocal frame_count
        try:
            while CAMERA_ACTIVE:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_count += 1

                # 诊断日志
                if frame_count % 30 == 0:
                    print(f"[Diagnostics] Current detection mode: {system_state.DETECTION_MODE}")
                
                time_diff = update_detection_time()
                processed_frame = frame.copy()

                # 根据当前模式决定处理方式 (All modes now use session-local models)
                if system_state.DETECTION_MODE == 'object_detection':
                    outputs = object_model_stream.track(processed_frame, persist=True)
                    detection_service.process_object_detection_results(outputs, processed_frame, time_diff, frame_count)
                
                elif system_state.DETECTION_MODE == 'fall_detection':
                    pose_results = pose_model_stream.track(processed_frame, persist=True)
                    detection_service.process_pose_estimation_results(pose_results, processed_frame, time_diff, frame_count)

                elif system_state.DETECTION_MODE == 'face_only':
                    # 修复：恢复 state 参数的传递，这是必须的
                    if 'face_model' not in face_recognition_cache:
                        face_recognition_cache['face_model'] = face_model_stream
                    detection_service.process_faces_only(processed_frame, frame_count, face_recognition_cache)
                
                elif system_state.DETECTION_MODE == 'smoking_detection':
                    face_results = face_model_stream.predict(processed_frame, verbose=False)
                    person_results = object_model_stream.track(processed_frame, persist=True, classes=[0], verbose=False)
                    detection_service.process_smoking_detection_hybrid(
                        processed_frame, person_results, face_results, smoking_model_service
                    )

                # 将处理后的帧编码为JPEG格式
                (flag, encodedImage) = cv2.imencode(".jpg", processed_frame)
                if not flag:
                    continue
                    
                # 以multipart格式产生输出帧
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                      bytearray(encodedImage) + b'\r\n')
        finally:
            # 确保无论如何都能释放摄像头
            print("释放摄像头资源...")
            cap.release()
            cv2.destroyAllWindows()
            
    # 返回一个包含视频流的HTTP响应
    return Response(generate(),
                    mimetype = "multipart/x-mixed-replace; boundary=frame")

def stop_video_feed_service():
    """停止摄像头视频流的服务函数"""
    global CAMERA_ACTIVE
    CAMERA_ACTIVE = False
    print("摄像头视频流已请求停止。")
    return True 