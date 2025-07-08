import os
import base64
import json
import numpy as np
from io import BytesIO
from PIL import Image
from flask import request, current_app, jsonify
from flask_restx import Namespace, Resource, fields
import dlib
import face_recognition

# --- dlib 模型初始化 ---
# 定义模型文件路径
# 我们假设这些模型文件被放在了 backend/dat/ 目录下
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'dat')
SHAPE_PREDICTOR_PATH = os.path.join(MODEL_DIR, 'shape_predictor_68_face_landmarks.dat')
FACE_REC_MODEL_PATH = os.path.join(MODEL_DIR, 'dlib_face_recognition_resnet_model_v1.dat')

# 检查模型文件是否存在
if not os.path.exists(SHAPE_PREDICTOR_PATH) or not os.path.exists(FACE_REC_MODEL_PATH):
    print("="*50)
    print("警告: Dlib 模型文件未找到！")
    print(f"请将 'shape_predictor_68_face_landmarks.dat' 和 'dlib_face_recognition_resnet_model_v1.dat' 文件下载并放置在以下目录中:")
    print(f"'{os.path.abspath(MODEL_DIR)}'")
    print("你可以从 http://dlib.net/files/ 下载。")
    print("人脸识别功能将无法正常工作。")
    print("="*50)
    # 设置模型为None，以避免在没有模型的情况下崩溃
    detector, sp, facerec = None, None, None
else:
    # 加载dlib的人脸检测器和模型
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
    facerec = dlib.face_recognition_model_v1(FACE_REC_MODEL_PATH)
    print("Dlib 人脸识别模型加载成功。")

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
REGISTERED_FACES_FILE = os.path.join(os.getcwd(), '..', 'registered_faces.json')

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
        if not all([detector, sp, facerec]):
             return {'error': 'Dlib模型未加载，无法注册人脸'}, 500

        data = request.json
        student_id = data['student_id']
        image_data = data['image']
        
        # 解码Base64图像
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            image_np = np.array(image)
            # dlib需要BGR格式，但Pillow默认是RGB，不过很多时候dlib也能处理
            # 如果检测效果不好，可以尝试转换： image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        except Exception as e:
            return {'error': f'图像解码失败: {str(e)}'}, 400
        
        # 使用dlib检测人脸
        faces = detector(image_np, 1)
        if len(faces) != 1:
            return {'error': f'未检测到人脸或检测到多个人脸 (检测到 {len(faces)} 个)'}, 400
        
        # 获取人脸关键点并计算特征向量
        shape = sp(image_np, faces[0])
        face_descriptor = facerec.compute_face_descriptor(image_np, shape)
        
        # 将dlib的vector转换为numpy数组，再转为列表以便JSON序列化
        face_descriptor_list = [x for x in face_descriptor]
        
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
        if not all([detector, sp, facerec]):
             return {'error': 'Dlib模型未加载，无法识别人脸'}, 500

        data = request.json
        image_data = data['image']
        
        # 解码Base64图像
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            image_np = np.array(image)
        except Exception as e:
            return {'error': f'图像解码失败: {str(e)}'}, 400
        
        # 检测人脸
        faces = detector(image_np, 1)
        if len(faces) == 0:
            return {'recognized': False, 'student_id': '未检测到人脸', 'confidence': 0.0}
        
        # 我们只处理检测到的第一个人脸
        face = faces[0]
        shape = sp(image_np, face)
        query_descriptor = np.array(facerec.compute_face_descriptor(image_np, shape))
        
        # 加载已注册的人脸数据
        registered_faces = load_registered_faces()
        if not registered_faces:
            return {'recognized': False, 'student_id': '陌生人 (数据库为空)', 'confidence': 0.0}
        
        # 准备数据进行比对
        known_descriptors = [np.array(desc) for desc in registered_faces.values()]
        student_ids = list(registered_faces.keys())
        
        # 使用face_recognition库的函数进行比对
        # 它计算欧氏距离并与阈值比较
        matches = face_recognition.compare_faces(known_descriptors, query_descriptor, tolerance=0.4)
        
        # 查找匹配结果
        if True in matches:
            # 如果有多个匹配，我们可以找到距离最近的那个
            face_distances = face_recognition.face_distance(known_descriptors, query_descriptor)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                student_id = student_ids[best_match_index]
                # 将距离转换为置信度（非线性转换）
                confidence = 1.0 - face_distances[best_match_index]
                return {'recognized': True, 'student_id': student_id, 'confidence': confidence}

        return {'recognized': False, 'student_id': '陌生人', 'confidence': 0.0} 