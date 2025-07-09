import cv2
import numpy as np
from ultralytics import YOLO
import os
import face_recognition

from app.services.danger_zone import DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD, TARGET_CLASSES
from app.services.alerts import (
    add_alert, update_loitering_time, reset_loitering_time, 
    update_detection_time, get_alerts, reset_alerts
)
from app.utils.geometry import point_in_polygon, distance_to_polygon
from app.services import face_service

# YOLO模型路径
MODEL_PATH = "yolov8n.pt"

def get_model():
    """获取YOLO模型实例"""
    return YOLO(MODEL_PATH)

def process_image(filepath, uploads_dir):
    """
    处理单张图片
    
    参数:
        filepath: 图片文件路径
        uploads_dir: 上传文件目录
        
    返回:
        dict: 包含处理结果的字典
    """
    # 读取图片
    img = cv2.imread(filepath)
    if img is None:
        return {"status": "error", "message": "Failed to load image"}, 500
    
    # 执行对象检测
    model = get_model()
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
    output_path = os.path.join(uploads_dir, output_filename)
    print(f"保存处理后的图像到: {output_path}")
    cv2.imwrite(output_path, res_plotted)
    
    # 使用相对URL路径
    output_url = f"/api/files/{output_filename}"
    print(f"图像处理完成，输出URL: {output_url}")
    
    return {
        "status": "success",
        "media_type": "image",
        "file_url": output_url,
        "alerts": get_alerts()
    }

def process_video(filepath, uploads_dir):
    """
    处理视频文件
    
    参数:
        filepath: 视频文件路径
        uploads_dir: 上传文件目录
        
    返回:
        dict: 包含处理结果的字典
    """
    # 重置警报
    reset_alerts()
    
    # 创建输出视频路径
    output_filename = 'processed_' + os.path.basename(filepath)
    output_path = os.path.join(uploads_dir, output_filename)
    print(f"处理视频: {filepath}")
    print(f"输出路径: {output_path}")
    
    # 打开视频
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return {"status": "error", "message": "Failed to open video"}, 500
    
    # 获取视频属性
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # 初始化YOLOv8模型
    model = get_model()
    
    # 为本次视频处理创建一个新的人脸识别缓存
    face_recognition_cache = {}
    
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
        time_diff = update_detection_time()
        
        # 执行目标追踪
        results = model.track(frame, persist=True)
        
        # 获取处理后的帧, 我们不再使用plot()，而是自己绘制
        processed_frame = frame.copy()
        
        # 绘制危险区域
        overlay = processed_frame.copy()
        danger_zone_pts = DANGER_ZONE.reshape((-1, 1, 2))
        cv2.fillPoly(overlay, [danger_zone_pts], (0, 0, 255))
        cv2.addWeighted(overlay, 0.4, processed_frame, 0.6, 0, processed_frame)
        cv2.polylines(processed_frame, [danger_zone_pts], True, (0, 0, 255), 3)
        
        # 在危险区域中添加文字
        danger_zone_center = np.mean(DANGER_ZONE, axis=0, dtype=np.int32)
        cv2.putText(processed_frame, "Danger Zone", 
                    (danger_zone_center[0] - 60, danger_zone_center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        # 处理检测结果
        process_detection_results(results, processed_frame, time_diff, frame_count, face_recognition_cache)
        
        # 写入处理后的帧到输出视频
        out.write(processed_frame)
    
    # 释放资源
    cap.release()
    out.release()
    
    # 使用相对URL路径
    output_url = f"/api/files/{output_filename}"
    print(f"视频处理完成，输出URL: {output_url}")
    
    return {
        "status": "success",
        "media_type": "video",
        "file_url": output_url,
        "alerts": get_alerts()
    }

def process_detection_results(results, frame, time_diff, frame_count, face_recognition_cache):
    """
    处理检测结果，更新警报状态并在帧上绘制信息
    
    参数:
        results: YOLO检测结果
        frame: 当前视频帧
        time_diff: 与上一帧的时间差
        frame_count: 当前的帧数，用于控制人脸识别频率
        face_recognition_cache: 用于缓存已识别人脸的字典
    """
    # 如果有追踪结果，在画面上显示追踪ID和危险区域告警
    if hasattr(results[0], 'boxes') and hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.int().cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        
        # 获取类别名称
        class_names = results[0].names
        
        for box, id, cls in zip(boxes, ids, classes):
            x1, y1, x2, y2 = box
            class_name = class_names[int(cls)]
            
            # 只处理指定类别的目标
            if int(cls) in TARGET_CLASSES:
                # ============== 人脸识别逻辑 (开始) ==============
                
                # 首先从缓存中获取名字
                face_name = face_recognition_cache.get(id)

                # 如果缓存中没有，并且是检查帧，则进行识别
                if face_name is None and frame_count % 10 == 0:
                    # 从帧中裁剪出人的区域
                    person_img = frame[int(y1):int(y2), int(x1):int(x2)]
                    
                    if person_img.size > 0:
                        # 将图像从BGR（OpenCV格式）转换为RGB（face_recognition格式）
                        rgb_person_img = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGB)
                        
                        # 查找人脸编码
                        face_locations = face_recognition.face_locations(rgb_person_img)
                        face_encodings = face_recognition.face_encodings(rgb_person_img, face_locations)

                        if face_encodings:
                            # 假设每个人只有一个面孔
                            identified_name = face_service.identify_face(face_encodings[0])
                            face_recognition_cache[id] = identified_name # 将结果存入缓存
                        else:
                            # 如果未找到人脸，也进行缓存，避免重复检查
                            face_recognition_cache[id] = "Unknown"
                
                # 再次从缓存获取名字
                face_name = face_recognition_cache.get(id)

                # ============== 人脸识别逻辑 (结束) ==============

                # 计算目标的底部中心点
                foot_point = (int((x1 + x2) / 2), int(y2))
                
                # 检查是否在危险区域内
                in_danger_zone = point_in_polygon(foot_point, DANGER_ZONE)
                
                # 计算到危险区域的距离
                distance = distance_to_polygon(foot_point, DANGER_ZONE)
                
                # 确定标签颜色和告警状态
                label_color = (0, 255, 0)  # 默认绿色
                alert_status = None
                
                display_name = class_name
                if face_name and face_name != "Unknown":
                    display_name = face_name
                elif face_name == "Unknown":
                    display_name = "Stranger"
                    add_alert(f"ID:{id} Detected as a stranger.")

                
                # 如果在危险区域内，更新停留时间
                if in_danger_zone:
                    loitering_time = update_loitering_time(id, time_diff)
                    
                    # 如果停留时间超过阈值，标记为红色并记录告警
                    if loitering_time >= LOITERING_THRESHOLD:
                        # 使用纯红色
                        label_color = (0, 0, 255)  # BGR格式：红色
                        alert_status = f"ID:{id} ({display_name}) staying in danger zone for {loitering_time:.1f}s"
                        add_alert(alert_status)
                    else:
                        # 根据停留时间从橙色到红色渐变
                        ratio = min(1.0, loitering_time / LOITERING_THRESHOLD)
                        # 从橙色(0,165,255)到红色(0,0,255)
                        label_color = (0, int(165 * (1 - ratio)), 255)
                else:
                    # 如果不在区域内，重置停留时间
                    reset_loitering_time(id)
                    
                    # 如果距离小于安全距离，根据距离设置颜色从绿色到黄色
                    if distance < SAFETY_DISTANCE:
                        # 计算距离比例
                        ratio = distance / SAFETY_DISTANCE
                        # 从黄色(0,255,255)到绿色(0,255,0)渐变
                        label_color = (0, 255, int(255 * (1 - ratio)))
                        
                        alert_status = f"ID:{id} ({display_name}) too close to danger zone ({distance:.1f}px)"
                        add_alert(alert_status)
                
                # 在每个目标上方显示ID和类别
                label = f"ID:{id} {display_name}"

                if in_danger_zone:
                    label += f" time:{get_loitering_time(id):.1f}s"
                elif distance < SAFETY_DISTANCE:
                    label += f" dist:{distance:.1f}px"
                
                # 根据危险程度调整边框粗细
                thickness = 2  # 默认粗细
                if in_danger_zone:
                    # 在危险区域内，根据停留时间增加边框粗细
                    thickness = max(2, int(4 * min(1.0, get_loitering_time(id) / LOITERING_THRESHOLD)))
                    
                    # 如果停留时间超过阈值，添加警告标记
                    if get_loitering_time(id) >= LOITERING_THRESHOLD:
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
                        
                        cv2.fillPoly(frame, [triangle_pts], (0, 0, 255))  # 红色填充
                        cv2.polylines(frame, [triangle_pts], True, (0, 0, 0), 1)  # 黑色边框
                        
                        # 在三角形中绘制感叹号
                        cv2.putText(frame, "!", 
                                    (triangle_center_x - 3, triangle_top_y + triangle_height - 5), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                elif distance < SAFETY_DISTANCE:
                    # 不在危险区域但接近时，根据距离增加边框粗细
                    thickness = max(1, int(3 * (1 - distance / SAFETY_DISTANCE)))
                
                # 绘制边框
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), label_color, thickness)
                
                # 绘制标签背景
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                cv2.rectangle(frame, (int(x1), int(y1) - h - 10), (int(x1) + w, int(y1) - 5), label_color, -1)
                
                # 绘制标签文本
                cv2.putText(frame, label, (int(x1), int(y1)-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # 在目标底部位置画一个点
                foot_point = (int((x1 + x2) / 2), int(y2))
                cv2.circle(frame, foot_point, 5, label_color, -1)
                
                # 如果不在危险区域内但距离小于安全距离的2倍，绘制到危险区域的连接线
                if not in_danger_zone and distance < SAFETY_DISTANCE * 2:
                    draw_distance_line(frame, foot_point, distance)

def draw_distance_line(frame, foot_point, distance):
    """
    绘制从目标到危险区域的连接线
    
    参数:
        frame: 当前视频帧
        foot_point: 目标的底部中心点
        distance: 目标到危险区域的距离
    """
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
        label_color = (0, 255, int(255 * (1 - distance / SAFETY_DISTANCE))) if distance < SAFETY_DISTANCE else (0, 255, 0)
        cv2.line(frame, foot_point, closest_point, label_color, line_thickness)
        
        # 在线上显示距离数字
        mid_point = ((foot_point[0] + closest_point[0]) // 2, 
                    (foot_point[1] + closest_point[1]) // 2)
        cv2.putText(frame, f"{distance:.1f}px", 
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
                    cv2.line(frame, start_point, end_point, (0, 0, 255), line_thickness + 1) 