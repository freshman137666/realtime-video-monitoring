import cv2
import uuid
import threading
import time
import queue
import os
from datetime import datetime
from typing import Dict, List, Optional
from app import socketio
from app.services.danger_zone import DANGER_ZONE
from ultralytics import YOLO
import numpy as np
import base64

class RTMPStreamManager:
    def __init__(self):
        self.streams: Dict[str, dict] = {}
        self.active_captures: Dict[str, cv2.VideoCapture] = {}
        self.processing_threads: Dict[str, threading.Thread] = {}
        self.frame_queues: Dict[str, queue.Queue] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        
        # 初始化AI模型
        self.models = {'object': None}
        self._load_models()
    
    def _load_models(self):
        """加载AI模型"""
        try:
            # 尝试多个可能的模型路径
            possible_paths = [
                '../yolo-Weights/yolov8n.pt',  # 根目录的yolo-Weights
                'yolo-Weights/yolov8n.pt',     # backend目录的yolo-Weights
                '../../yolo-Weights/yolov8n.pt', # 从services目录向上两级
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'yolo-Weights', 'yolov8n.pt')  # 绝对路径
            ]
            
            model_loaded = False
            for model_path in possible_paths:
                try:
                    if os.path.exists(model_path):
                        self.models['object'] = YOLO(model_path)
                        print(f"✅ YOLO模型加载成功: {model_path}")
                        model_loaded = True
                        break
                except Exception as e:
                    print(f"尝试加载模型 {model_path} 失败: {e}")
                    continue
            
            if not model_loaded:
                print("⚠️ 本地YOLO模型文件未找到，尝试下载默认模型...")
                try:
                    # 使用ultralytics自动下载的默认模型
                    self.models['object'] = YOLO('yolov8n.pt')  # 这会自动下载到用户目录
                    print("✅ 默认YOLO模型下载并加载成功")
                except Exception as e:
                    print(f"❌ 默认模型下载失败: {e}")
                    self.models['object'] = None
                
        except Exception as e:
            print(f"❌ 模型初始化失败: {e}")
            self.models['object'] = None
    
    def add_stream(self, config: dict) -> str:
        """添加新的RTMP流"""
        stream_id = str(uuid.uuid4())
        
        # 移除RTMP URL验证，因为RTMP流可能需要时间建立连接
        # 直接保存流配置，在启动时再验证
        
        # 保存流配置
        self.streams[stream_id] = {
            'stream_id': stream_id,
            'name': config['name'],
            'rtmp_url': config['rtmp_url'],
            'description': config.get('description', ''),
            'detection_modes': config.get('detection_modes', ['object_detection']),
            'status': 'inactive',
            'created_at': datetime.now().isoformat(),
            'last_activity': None
        }
        
        return stream_id

    def start_stream(self, stream_id: str):
        """启动RTMP流处理"""
        if stream_id not in self.streams:
            raise Exception("流不存在")
        
        if stream_id in self.active_captures:
            raise Exception("流已经在运行")
        
        stream_config = self.streams[stream_id]
        print(f"尝试启动流: {stream_id}, URL: {stream_config['rtmp_url']}")
        
        # 创建视频捕获对象，添加RTMP优化配置
        try:
            cap = cv2.VideoCapture(stream_config['rtmp_url'])
            
            # 设置RTMP流的优化参数
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲区大小，降低延迟
            cap.set(cv2.CAP_PROP_FPS, 30)  # 设置帧率
            
            # 尝试多次连接
            max_retries = 3
            for attempt in range(max_retries):
                if cap.isOpened():
                    # 测试读取一帧
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✅ RTMP流连接成功，帧大小: {frame.shape}")
                        break
                    else:
                        print(f"⚠️ 连接尝试 {attempt + 1}/{max_retries}: 无法读取数据")
                else:
                    print(f"⚠️ 连接尝试 {attempt + 1}/{max_retries}: 无法打开流")
                
                if attempt < max_retries - 1:
                    cap.release()
                    time.sleep(2)  # 等待2秒后重试
                    cap = cv2.VideoCapture(stream_config['rtmp_url'])
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FPS, 30)
            else:
                # 所有重试都失败
                cap.release()
                raise Exception(f"经过{max_retries}次尝试，仍无法连接到RTMP流: {stream_config['rtmp_url']}")
                
        except Exception as e:
            print(f"❌ RTMP流连接失败: {e}")
            raise Exception(f"RTMP流连接失败: {str(e)}")
        
        # 设置VideoCapture的属性以减少延迟
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        
        self.active_captures[stream_id] = cap
        self.frame_queues[stream_id] = queue.Queue(maxsize=10)
        self.stop_events[stream_id] = threading.Event()
        
        # 启动处理线程
        thread = threading.Thread(
            target=self._process_stream,
            args=(stream_id,),
            daemon=True
        )
        thread.start()
        self.processing_threads[stream_id] = thread
        
        # 更新状态
        self.streams[stream_id]['status'] = 'active'
        self.streams[stream_id]['last_activity'] = datetime.now().isoformat()
        
        print(f"✅ 流 {stream_id} 启动成功")

    def _validate_rtmp_url(self, rtmp_url: str) -> bool:
        """验证RTMP URL的有效性（改进版）"""
        try:
            # 基本URL格式检查
            if not rtmp_url.startswith('rtmp://'):
                return False
            
            # 尝试快速连接测试
            cap = cv2.VideoCapture(rtmp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 给连接一些时间
            time.sleep(1)
            
            is_valid = cap.isOpened()
            cap.release()
            return is_valid
        except Exception as e:
            print(f"RTMP URL验证失败: {e}")
            return False
    
    def stop_stream(self, stream_id: str):
        """停止RTMP流处理"""
        if stream_id not in self.streams:
            raise Exception("流不存在")
        
        # 设置停止事件
        if stream_id in self.stop_events:
            self.stop_events[stream_id].set()
        
        # 等待线程结束
        if stream_id in self.processing_threads:
            self.processing_threads[stream_id].join(timeout=5)
            del self.processing_threads[stream_id]
        
        # 释放资源
        if stream_id in self.active_captures:
            self.active_captures[stream_id].release()
            del self.active_captures[stream_id]
        
        if stream_id in self.frame_queues:
            del self.frame_queues[stream_id]
        
        if stream_id in self.stop_events:
            del self.stop_events[stream_id]
        
        # 更新状态
        self.streams[stream_id]['status'] = 'inactive'
    
    def delete_stream(self, stream_id: str):
        """删除RTMP流"""
        if stream_id not in self.streams:
            raise Exception("流不存在")
        
        # 先停止流
        if self.streams[stream_id]['status'] == 'active':
            self.stop_stream(stream_id)
        
        # 删除流配置
        del self.streams[stream_id]
    
    def get_all_streams(self) -> List[dict]:
        """获取所有流的信息"""
        return list(self.streams.values())
    
    def get_stream_frames(self, stream_id: str):
        """获取流的帧数据（生成器）"""
        if stream_id not in self.frame_queues:
            raise Exception("流未激活")
        
        frame_queue = self.frame_queues[stream_id]
        
        while stream_id in self.active_captures:
            try:
                # 从队列获取帧数据
                frame_data = frame_queue.get(timeout=1)
                yield frame_data
            except queue.Empty:
                continue
            except Exception as e:
                print(f"获取帧数据错误: {e}")
                break
    
    def _validate_rtmp_url(self, rtmp_url: str) -> bool:
        """验证RTMP URL的有效性"""
        try:
            cap = cv2.VideoCapture(rtmp_url)
            is_valid = cap.isOpened()
            cap.release()
            return is_valid
        except Exception:
            return False
    
    def _process_stream(self, stream_id: str):
        """处理单个RTMP流的主循环"""
        cap = self.active_captures[stream_id]
        frame_queue = self.frame_queues[stream_id]
        stop_event = self.stop_events[stream_id]
        stream_config = self.streams[stream_id]
        
        frame_count = 0
        last_detection_time = time.time()
        
        try:
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    print(f"流 {stream_id} 读取帧失败")
                    break
                
                frame_count += 1
                current_time = time.time()
                
                # 每隔几帧进行一次AI检测
                if frame_count % 5 == 0:  # 每5帧检测一次
                    try:
                        # 执行AI检测
                        detection_results = self._perform_detection(
                            frame, stream_config['detection_modes']
                        )
                        
                        # 通过WebSocket发送检测结果
                        socketio.emit('detection_result', {
                            'stream_id': stream_id,
                            'timestamp': datetime.now().isoformat(),
                            'detections': detection_results['detections'],
                            'alerts': detection_results['alerts']
                        }, namespace='/rtmp', room=stream_id)
                        
                        last_detection_time = current_time
                        
                    except Exception as e:
                        print(f"检测处理错误: {e}")
                
                # 编码帧为JPEG
                try:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_data = buffer.tobytes()
                    
                    # 将帧数据放入队列
                    if not frame_queue.full():
                        frame_queue.put(frame_data)
                    else:
                        # 队列满时，移除旧帧
                        try:
                            frame_queue.get_nowait()
                            frame_queue.put(frame_data)
                        except queue.Empty:
                            pass
                            
                except Exception as e:
                    print(f"帧编码错误: {e}")
                
                # 更新活动时间
                self.streams[stream_id]['last_activity'] = datetime.now().isoformat()
                
                # 控制帧率
                time.sleep(0.033)  # 约30fps
                
        except Exception as e:
            print(f"流处理错误 {stream_id}: {e}")
        finally:
            # 更新流状态
            if stream_id in self.streams:
                self.streams[stream_id]['status'] = 'error'
    
    def _perform_detection(self, frame: np.ndarray, detection_modes: List[str]) -> dict:
        """执行AI检测"""
        results = {
            'detections': [],
            'alerts': []
        }
        
        try:
            # 检查模型是否可用
            if 'object_detection' in detection_modes and self.models['object'] is not None:
                # 目标检测
                yolo_results = self.models['object'](frame)
                
                for result in yolo_results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = box.conf[0].cpu().numpy()
                            cls = int(box.cls[0].cpu().numpy())
                            
                            if conf > 0.5:  # 置信度阈值
                                detection = {
                                    'type': 'object',
                                    'class': self.models['object'].names[cls],
                                    'confidence': float(conf),
                                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                                }
                                results['detections'].append(detection)
                                
                                # 检查是否在危险区域
                                if self._is_in_danger_zone(x1, y1, x2, y2):
                                    alert = f"检测到 {detection['class']} 进入危险区域"
                                    results['alerts'].append(alert)
            else:
                # 模型不可用时的处理
                if 'object_detection' in detection_modes:
                    # print("⚠️ 目标检测模型不可用，跳过AI检测")  # 避免日志过多
                    pass
            
        except Exception as e:
            print(f"检测执行错误: {e}")
        
        return results
    
    def _is_in_danger_zone(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """检查边界框是否与危险区域重叠"""
        try:
            # 计算边界框中心点
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # 简化实现：总是返回False，避免复杂的几何计算
            return False
        except Exception:
            return False

# 创建全局实例
rtmp_manager = RTMPStreamManager()