import cv2
import numpy as np
import os
from flask import Response
from ultralytics import YOLO

from app.services.danger_zone import DANGER_ZONE

def generate_video_feed():
    """
    生成实时视频流
    
    返回:
        generator: 视频帧生成器
    """
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
    
    try:
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
    finally:
        # --- 健壮性检查 3: 确保在循环结束后释放摄像头 ---
        print("释放摄像头资源。")
        cap.release()

def video_feed():
    """
    提供视频流响应
    
    返回:
        Response: Flask响应对象，包含视频流
    """
    return Response(generate_video_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 