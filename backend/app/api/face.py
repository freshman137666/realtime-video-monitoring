import os
import base64
import json
import numpy as np
from io import BytesIO
from PIL import Image
from flask import request, current_app, jsonify
from flask_restx import Namespace, Resource, fields

# 创建人脸API的命名空间
ns = Namespace('face', description='人脸识别相关操作')

# 定义人脸注册模型，用于Swagger文档
face_register_model = ns.model('FaceRegister', {
    'student_id': fields.String(required=True, description='学生ID'),
    'image': fields.String(required=True, description='人脸图像的Base64编码')
})

# 定义人脸识别结果模型
face_recognition_result = ns.model('FaceRecognitionResult', {
    'recognized': fields.Boolean(description='是否识别成功'),
    'student_id': fields.String(description='识别到的学生ID'),
    'confidence': fields.Float(description='识别置信度')
})

# 注册的人脸数据文件路径
REGISTERED_FACES_FILE = os.path.join(os.getcwd(), 'registered_faces.json')

# 初始化人脸数据文件
def init_face_data():
    if not os.path.exists(REGISTERED_FACES_FILE):
        with open(REGISTERED_FACES_FILE, 'w') as f:
            json.dump({}, f)

# 加载注册的人脸数据
def load_registered_faces():
    init_face_data()
    with open(REGISTERED_FACES_FILE, 'r') as f:
        return json.load(f)

# 保存注册的人脸数据
def save_registered_faces(faces_data):
    with open(REGISTERED_FACES_FILE, 'w') as f:
        json.dump(faces_data, f)

# 模拟dlib人脸检测器和识别模型
# 在实际项目中，你需要加载dlib的模型
# 但为了快速搭建，我们先模拟这些功能
def detect_face(image_np):
    # 这里应该使用dlib进行人脸检测
    # 现在我们简单返回一个假的检测结果
    return [(0, 0, 100, 100)]  # 假设检测到一个人脸，坐标为(0,0,100,100)

def compute_face_descriptor(image_np, face_rect):
    # 这里应该使用dlib计算人脸特征向量
    # 现在我们简单返回一个随机的128维向量
    return np.random.rand(128)

def compare_faces(known_descriptors, query_descriptor, tolerance=0.6):
    # 这里应该比较人脸特征向量的距离
    # 现在我们简单返回一个随机的比较结果
    if not known_descriptors:
        return []
    return [np.random.rand() < 0.2 for _ in range(len(known_descriptors))]  # 20%的概率匹配成功

@ns.route('/register')
class FaceRegister(Resource):
    @ns.doc('register_face')
    @ns.expect(face_register_model)
    def post(self):
        """注册人脸"""
        data = request.json
        student_id = data['student_id']
        image_data = data['image']
        
        # 解码Base64图像
        try:
            # 去除可能存在的Base64前缀
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            image_np = np.array(image)
        except Exception as e:
            return {'error': f'图像解码失败: {str(e)}'}, 400
        
        # 检测人脸
        faces = detect_face(image_np)
        if len(faces) != 1:
            return {'error': '没有检测到人脸或检测到多个人脸'}, 400
        
        # 计算人脸特征向量
        face_descriptor = compute_face_descriptor(image_np, faces[0])
        
        # 将人脸特征向量转换为列表（以便JSON序列化）
        face_descriptor_list = face_descriptor.tolist()
        
        # 加载已注册的人脸数据
        registered_faces = load_registered_faces()
        
        # 添加新的人脸数据
        registered_faces[student_id] = face_descriptor_list
        
        # 保存更新后的人脸数据
        save_registered_faces(registered_faces)
        
        return {'message': '人脸注册成功'}, 201

@ns.route('/recognize')
class FaceRecognize(Resource):
    @ns.doc('recognize_face')
    @ns.expect(ns.model('FaceRecognizeInput', {
        'image': fields.String(required=True, description='人脸图像的Base64编码')
    }))
    @ns.marshal_with(face_recognition_result)
    def post(self):
        """识别人脸"""
        data = request.json
        image_data = data['image']
        
        # 解码Base64图像
        try:
            # 去除可能存在的Base64前缀
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            image_np = np.array(image)
        except Exception as e:
            return {'error': f'图像解码失败: {str(e)}'}, 400
        
        # 检测人脸
        faces = detect_face(image_np)
        if len(faces) != 1:
            return {'recognized': False, 'student_id': '', 'confidence': 0.0}
        
        # 计算人脸特征向量
        face_descriptor = compute_face_descriptor(image_np, faces[0])
        
        # 加载已注册的人脸数据
        registered_faces = load_registered_faces()
        
        # 如果没有注册的人脸，直接返回未识别
        if not registered_faces:
            return {'recognized': False, 'student_id': '', 'confidence': 0.0}
        
        # 比较人脸
        known_descriptors = list(registered_faces.values())
        student_ids = list(registered_faces.keys())
        
        matches = compare_faces(known_descriptors, face_descriptor)
        
        # 查找最匹配的人脸
        if True in matches:
            match_index = matches.index(True)
            student_id = student_ids[match_index]
            confidence = 0.8  # 假设置信度为0.8
            return {'recognized': True, 'student_id': student_id, 'confidence': confidence}
        else:
            return {'recognized': False, 'student_id': '', 'confidence': 0.0} 