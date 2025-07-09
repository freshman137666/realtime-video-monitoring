import face_recognition
import numpy as np
import os
import json

# 定义用于存储人脸编码的路径
# data目录位于项目的根目录下
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'data')
ENCODINGS_FILE = os.path.join(DATA_DIR, 'face_encodings.json')

# 已知人脸的内存缓存
known_face_encodings = []
known_face_names = []

def _ensure_data_dir_exists():
    """确保data目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)

def load_known_faces():
    """从JSON文件加载人脸编码和姓名到内存中"""
    global known_face_encodings, known_face_names
    _ensure_data_dir_exists()
    
    if os.path.exists(ENCODINGS_FILE):
        try:
            with open(ENCODINGS_FILE, 'r') as f:
                data = json.load(f)
                known_face_names = [item['name'] for item in data]
                # JSON将numpy数组保存为列表，需要将其转换回来
                known_face_encodings = [np.array(item['encoding']) for item in data]
            print(f"加载了 {len(known_face_names)} 个已知人脸。")
        except (json.JSONDecodeError, KeyError):
            # 如果文件损坏或格式不正确，则重新开始
            known_face_encodings = []
            known_face_names = []
            print("人脸数据文件已损坏或格式不正确。将重新开始。")
    else:
        # 如果文件不存在，则使用空列表进行初始化
        known_face_encodings = []
        known_face_names = []
        print("未找到已知人脸文件。将重新开始。")

def save_known_faces():
    """将当前内存中的已知人脸保存到JSON文件中"""
    _ensure_data_dir_exists()
    
    data_to_save = []
    for encoding, name in zip(known_face_encodings, known_face_names):
        data_to_save.append({
            'name': name,
            # 将numpy数组转换为列表以进行JSON序列化
            'encoding': encoding.tolist()
        })
        
    with open(ENCODINGS_FILE, 'w') as f:
        json.dump(data_to_save, f, indent=4)
    print(f"已将 {len(data_to_save)} 个人脸保存到 {ENCODINGS_FILE}。")
    return True

def register_new_face(image_path, name):
    """
    从图像文件注册新的人脸。
    参数:
        image_path (str): 图像文件的路径。
        name (str): 人员的姓名。
    返回:
        dict: 一个表示成功或失败的字典。
    """
    if name in known_face_names:
        return {"status": "error", "message": f"'{name}' 已被注册。"}

    image = face_recognition.load_image_file(image_path)
    # 模型可能会检测到多个人脸，我们使用找到的第一个。
    # 为获得更好的结果，请确保注册照片中只有一张清晰的人脸。
    face_encodings = face_recognition.face_encodings(image)

    if not face_encodings:
        return {"status": "error", "message": "在图像中未找到人脸。"}
    
    if len(face_encodings) > 1:
        return {"status": "error", "message": "在图像中找到多个人脸。请使用只有单一人脸的照片。"}

    # 将新的人脸添加到我们的内存列表中
    known_face_encodings.append(face_encodings[0])
    known_face_names.append(name)
    
    # 将更新后的列表保存到文件中
    save_known_faces()
    
    return {"status": "success", "message": f"'{name}' 的人脸已成功注册。"}

def identify_face(unknown_encoding):
    """
    通过与已知人脸进行比较来识别人脸。
    参数:
        unknown_encoding: 要识别的人脸编码。
    返回:
        str: 匹配到的人员姓名或“Unknown”。
    """
    if not known_face_encodings:
        return "Unknown"
        
    # 将 NumPy 数组列表转换为单个 NumPy 数组
    known_face_encodings_np = np.array(known_face_encodings)
    
    # 计算当前人脸与所有已知人脸的距离
    face_distances = face_recognition.face_distance(known_face_encodings_np, unknown_encoding)
    
    # 找到距离最近的人脸
    best_match_index = np.argmin(face_distances)
    
    # 获取最佳匹配的距离值
    best_distance = face_distances[best_match_index]
    
    # 假设我们设定一个阈值，例如 0.4。距离越小越相似。
    # 这个阈值可以根据实际效果调整。
    if best_distance < 0.4:
        name = known_face_names[best_match_index]
        print(f"识别到人脸: {name}, 距离: {best_distance:.2f}")
        return name, best_distance # 返回名字和距离
    
    print(f"未识别到匹配的人脸，最近距离: {best_distance:.2f}")
    return "Unknown", best_distance # 即使未知，也返回最近距离

def get_all_registered_names():
    """返回所有已注册姓名的列表"""
    return known_face_names

def delete_face(name):
    """
    按姓名删除已注册的人脸。
    参数:
        name (str): 要删除的人员的姓名。
    返回:
        bool: 如果删除成功则返回True，否则返回False。
    """
    global known_face_encodings, known_face_names
    
    if name not in known_face_names:
        return False

    # 创建不包括要删除人员的新列表
    new_encodings = []
    new_names = []
    for encoding, current_name in zip(known_face_encodings, known_face_names):
        if current_name != name:
            new_encodings.append(encoding)
            new_names.append(current_name)
    
    known_face_encodings = new_encodings
    known_face_names = new_names
    
    save_known_faces()
    return True

# 在模块启动时从文件加载已知人脸
load_known_faces() 