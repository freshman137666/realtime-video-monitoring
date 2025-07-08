import os
import cv2
import time
import numpy as np
from flask import Response, request, current_app, jsonify
from flask_restx import Namespace, Resource, fields
from werkzeug.utils import secure_filename
from app import db
from app.models import Alert
from ultralytics import YOLO
import datetime
import json
from collections import defaultdict
import math

# 创建视频API的命名空间
ns = Namespace('video', description='视频流处理相关操作')

# 从运行文件中导入YOLO模型
# 注意：这不是最佳实践，但为了快速迁移，我们先这样做
# 在真正的生产环境中，我们应该使用单例模式或应用上下文来管理模型
from run import yolo_model

# 定义全局变量
# 危险区域的多边形坐标 (x, y) 格式
CONFIG_FILE = os.path.join(os.getcwd(), '..', 'danger_zone_config.json')

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

# 加载配置
DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD = load_danger_zone_config()

# 需要检测的目标类别 (扩展到人和车辆)
TARGET_CLASSES = [0, 2, 7]  # person, car, truck

# 用于跟踪目标在危险区域内的停留时间
target_loitering_time = defaultdict(float)

# 上次检测的时间戳
last_detection_time = time.time()

# 定义一些Swagger文档模型
config_model = ns.model('Config', {
    'danger_zone': fields.List(fields.List(fields.Integer), description='危险区域多边形坐标'),
    'safety_distance': fields.Integer(description='安全距离', default=100),
    'loitering_threshold': fields.Float(description='停留时间阈值', default=2.0)
})

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

def gen_frames(stream_id):
    """生成视频帧"""
    global DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD, target_loitering_time, last_detection_time
    
    # 在实际项目中，这里应该根据stream_id从RTMP服务器获取视频流
    # 为了快速适配前端，我们暂时使用默认摄像头
    cap = cv2.VideoCapture(0)  # 使用本地摄像头
    
    # 设置分辨率为480*480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frame_skip = 3  # 跳过的帧数
    frame_count = 0
    
    while True:
        success, frame = cap.read()
        if not success:
            break
            
        if frame_count % frame_skip == 0:
            # 当前时间戳
            current_time = time.time()
            time_diff = current_time - last_detection_time
            last_detection_time = current_time
            
            # 目标检测
            if yolo_model:
                # 使用YOLO进行目标检测
                results = yolo_model.predict(frame, classes=TARGET_CLASSES, verbose=False)
                
                # 在图像上绘制危险区域
                cv2.polylines(frame, [DANGER_ZONE], True, (0, 0, 255), 2)
                
                # 处理每个检测到的对象
                if len(results) > 0:
                    boxes = results[0].boxes
                    
                    for i, box in enumerate(boxes):
                        # 获取检测框坐标
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        # 计算底部中点坐标（假设物体站在地面上）
                        bottom_center = (int((x1 + x2) / 2), y2)
                        
                        # 检查是否在危险区域内
                        in_danger_zone = point_in_polygon(bottom_center, DANGER_ZONE)
                        
                        # 计算到危险区域边缘的距离
                        distance = distance_to_polygon(bottom_center, DANGER_ZONE)
                        
                        # 获取物体类别
                        cls = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # 获取类别名称
                        class_name = yolo_model.names[cls]
                        
                        # 设置绘制颜色和告警状态
                        color = (0, 255, 0)  # 默认绿色
                        alarm_text = ""
                        
                        # 对象唯一标识，用于跟踪停留时间
                        obj_id = f"{cls}_{i}_{x1}_{y1}"
                        
                        if in_danger_zone:
                            # 更新对象在危险区域的停留时间
                            if obj_id in target_loitering_time:
                                target_loitering_time[obj_id] += time_diff
                            else:
                                target_loitering_time[obj_id] = 0
                                
                            # 如果停留时间超过阈值，触发告警
                            if target_loitering_time[obj_id] > LOITERING_THRESHOLD:
                                color = (0, 0, 255)  # 红色表示告警
                                alarm_text = f"ALARM: {class_name} in danger zone"
                                
                                # 生成告警记录
                                # 保存告警截图
                                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                image_filename = f"alert_{timestamp}.jpg"
                                image_path = os.path.join(os.getcwd(), "uploads", image_filename)
                                
                                # 确保uploads文件夹存在
                                os.makedirs(os.path.join(os.getcwd(), "uploads"), exist_ok=True)
                                
                                cv2.imwrite(image_path, frame)
                                
                                # 创建告警记录
                                alert = Alert(
                                    alert_type="入侵危险区域",
                                    description=f"{class_name}进入危险区域并停留{target_loitering_time[obj_id]:.1f}秒",
                                    image_path=image_filename
                                )
                                
                                # 在实际项目中，这里应该将告警记录添加到数据库
                                # db.session.add(alert)
                                # db.session.commit()
                        elif distance < SAFETY_DISTANCE:
                            color = (0, 165, 255)  # 橙色表示警告
                            alarm_text = f"WARNING: {class_name} near danger zone"
                        else:
                            # 如果物体不在危险区域，重置停留时间
                            target_loitering_time[obj_id] = 0
                        
                        # 绘制边界框
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # 绘制类别名称和置信度
                        label = f"{class_name} {confidence:.2f}"
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        # 绘制告警文本
                        if alarm_text:
                            cv2.putText(frame, alarm_text, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 编码图像
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            frame_bytes = buffer.tobytes()
            
            # 构造响应体
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        frame_count += 1

# 定义API路由
@ns.route('/feed/<string:stream_id>')
@ns.param('stream_id', '视频流ID')
class VideoFeed(Resource):
    @ns.doc('get_video_feed')
    def get(self, stream_id):
        """获取实时视频流"""
        return Response(gen_frames(stream_id),
                       mimetype='multipart/x-mixed-replace; boundary=frame')

@ns.route('/config')
class VideoConfig(Resource):
    @ns.doc('get_video_config')
    @ns.marshal_with(config_model)
    def get(self):
        """获取视频处理配置"""
        return {
            'danger_zone': DANGER_ZONE.tolist(),
            'safety_distance': SAFETY_DISTANCE,
            'loitering_threshold': LOITERING_THRESHOLD
        }
    
    @ns.doc('update_video_config')
    @ns.expect(config_model)
    @ns.marshal_with(config_model)
    def put(self):
        """更新视频处理配置"""
        global DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD
        data = request.json
        
        if 'danger_zone' in data:
            DANGER_ZONE = np.array(data['danger_zone'], np.int32)
        
        if 'safety_distance' in data:
            SAFETY_DISTANCE = int(data['safety_distance'])
        
        if 'loitering_threshold' in data:
            LOITERING_THRESHOLD = float(data['loitering_threshold'])
        
        # 保存配置
        save_danger_zone_config(DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD)
        
        return {
            'danger_zone': DANGER_ZONE.tolist(),
            'safety_distance': SAFETY_DISTANCE,
            'loitering_threshold': LOITERING_THRESHOLD
        } 