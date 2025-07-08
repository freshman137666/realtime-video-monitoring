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
import dlib
from .face import registered_faces, detector, sp, facerec  # 从face.py导入所需变量和模型

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

# 视频处理和推流的核心函数
def gen_frames(stream_id):
    """
    从RTMP流读取视频，进行实时人脸识别，并生成帧。
    """
    stream_url = f'rtmp://127.0.0.1:9090/live/{stream_id}' # 根据老师要求，将端口修改为9090
    # 注意：这里的IP地址127.0.0.1表示RTMP服务器与后端服务运行在同一台机器上
    
    cap = cv2.VideoCapture(stream_url)
    
    # 按照老师要求设置帧率和跳帧
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) # 稍微调大一点以获得更好效果
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    frame_skip = 5  # 跳过的帧数
    frame_count = 0

    if not cap.isOpened():
        print(f"错误：无法打开RTMP视频流: {stream_url}")
        # 如果无法打开，可以返回一个提示错误的图片
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, f"Cannot open stream: {stream_id}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        return

    while True:
        success, frame = cap.read()
        if not success:
            print("视频流结束或读取失败。")
            break

        frame_count += 1
        if frame_count % frame_skip == 0:
            # 1. 转换为灰度图像
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 2. 检测人脸
            faces = detector(gray, 0) # 使用0表示不进行上采样，加快速度

            for face in faces:
                # 获取人脸关键点
                shape = sp(frame, face)
                # 计算人脸的128维编码
                face_encoding = np.array(facerec.compute_face_descriptor(frame, shape))
                
                # 比较捕获的人脸与已注册人脸库中的编码
                if registered_faces: # 确保库不为空
                    known_face_encodings = list(registered_faces.values())
                    student_ids = list(registered_faces.keys())
                    
                    matches = np.linalg.norm(np.array(known_face_encodings) - face_encoding, axis=1) <= 0.4
                    
                    name = "Stranger"
                    color = (0, 0, 255)  # 默认红色标记陌生人

                    if True in matches:
                        first_match_index = np.argmin(matches) if np.any(matches) else -1
                        if matches[first_match_index]:
                            student_id = student_ids[first_match_index]
                            name = student_id
                            color = (0, 255, 0)  # 绿色标记已注册人脸

                    # 在人脸周围绘制矩形框
                    (x, y, w, h) = (face.left(), face.top(), face.width(), face.height())
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    # 添加文本标签
                    cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        # 3. 编码图像并推流
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()


# 定义API路由
@ns.route('/feed/<string:stream_id>')
@ns.param('stream_id', '视频流ID')
class VideoFeed(Resource):
    @ns.doc('get_video_feed')
    def get(self, stream_id):
        """视频推流接口，处理指定ID的RTMP流并返回实时人脸识别结果"""
        return Response(gen_frames(stream_id), mimetype='multipart/x-mixed-replace; boundary=frame')

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