import dlib
import numpy as np
import cv2
import pandas as pd
import os
import logging
import csv

# --- Dlib 模型和数据路径定义 ---
# 所有路径都应相对于 `backend/dlib_data` 目录构建
DLIB_BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'dlib_data')

# 模型文件位于 dlib_data/data_dlib/
SHAPE_PREDICTOR_PATH = os.path.join(DLIB_BASE_DIR, 'data_dlib', 'shape_predictor_68_face_landmarks.dat')
FACE_REC_MODEL_PATH = os.path.join(DLIB_BASE_DIR, 'data_dlib', 'dlib_face_recognition_resnet_model_v1.dat')

# 注册的人脸图片存储在 dlib_data/data_faces_from_camera/
FACES_DIR = os.path.join(DLIB_BASE_DIR, 'data_faces_from_camera')

# 特征文件位于 dlib_data/
FEATURES_CSV_PATH = os.path.join(DLIB_BASE_DIR, 'features_all.csv')


# --- Dlib 人脸识别服务类 ---
class DlibFaceService:
    def __init__(self):
        """
        初始化服务，加载所有必要的模型和数据。
        """
        logging.info("正在初始化 Dlib 人脸识别服务...")

        # 1. 加载 Dlib 模型
        try:
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
            self.face_reco_model = dlib.face_recognition_model_v1(FACE_REC_MODEL_PATH)
            logging.info("Dlib 模型加载成功。")
        except Exception as e:
            logging.error(f"加载 Dlib 模型失败: {e}")
            raise RuntimeError(f"无法加载Dlib模型，请检查路径: {SHAPE_PREDICTOR_PATH} 和 {FACE_REC_MODEL_PATH}")

        # 2. 加载已知人脸特征数据库
        self.face_feature_known_list = []
        self.face_name_known_list = []
        self.load_face_database()
    
    def load_face_database(self):
        """
        从 features_all.csv 加载所有已知的人脸特征到内存中。
        """
        if os.path.exists(FEATURES_CSV_PATH) and os.path.getsize(FEATURES_CSV_PATH) > 0:
            try:
                csv_rd = pd.read_csv(FEATURES_CSV_PATH, header=None)
                self.face_name_known_list = []
                self.face_feature_known_list = []
                for i in range(csv_rd.shape[0]):
                    # 第一列是姓名
                    self.face_name_known_list.append(csv_rd.iloc[i][0])
                    # 后面的128列是特征
                    features = [float(x) for x in csv_rd.iloc[i][1:].values]
                    self.face_feature_known_list.append(features)
                logging.info(f"成功从 CSV 加载 {len(self.face_name_known_list)} 个已知人脸特征。")
            except Exception as e:
                logging.error(f"从 CSV 加载特征时出错: {e}")
        else:
            logging.warning(f"特征文件 '{FEATURES_CSV_PATH}' 不存在或为空。")

    def identify_faces(self, frame, face_boxes):
        """
        在给定的图像帧中识别人脸。
        参数:
            frame (np.ndarray): OpenCV 格式的图像帧。
            face_boxes (list): 由另一个检测器（如YOLOv8）提供的人脸边界框列表。
                               每个边界框格式为 (left, top, right, bottom)。
        返回:
            list: 包含识别结果的列表，每个元素是 (name, box)。
        """
        recognized_faces = []
        if not self.face_name_known_list:
            # 如果数据库为空，直接返回未识别结果
            for box in face_boxes:
                recognized_faces.append(("Unknown", box))
            return recognized_faces

        for box in face_boxes:
            # 修复：确保坐标是整数，以防止 Dlib 的 TypeError
            left, top, right, bottom = [int(p) for p in box]
            dlib_rect = dlib.rectangle(left, top, right, bottom)
            
            # 提取特征
            shape = self.predictor(frame, dlib_rect)
            features = self.face_reco_model.compute_face_descriptor(frame, shape)
            features = np.array(features)
            
            # 与数据库中的特征进行比较
            distances = np.linalg.norm(np.array(self.face_feature_known_list) - features, axis=1)
            
            # 寻找最佳匹配
            if len(distances) > 0:
                min_index = np.argmin(distances)
                min_distance = distances[min_index]
                
                # Dlib 推荐的阈值是 0.6，但 0.4 更严格，可以减少误报
                if min_distance < 0.4:
                    name = self.face_name_known_list[min_index]
                    # 确保返回的是原始的box，而不是dlib_rect
                    recognized_faces.append((name, box))
                else:
                    recognized_faces.append(("Unknown", box))
            else:
                recognized_faces.append(("Unknown", box))
        
        return recognized_faces

    def get_all_registered_names(self):
        """
        从内存中返回所有不重复的已注册姓名。
        """
        return sorted(list(set(self.face_name_known_list)))

    def delete_face_by_name(self, name):
        """
        根据姓名删除注册的人脸数据，包括图片和特征。
        参数:
            name (str): 要删除的人员姓名。
        返回:
            bool: 是否成功删除。
        """
        person_dir = os.path.join(FACES_DIR, name)
        if not os.path.exists(person_dir):
            logging.warning(f"要删除的目录 {person_dir} 不存在。")
            return False

        try:
            # 1. 删除图片文件夹
            import shutil
            shutil.rmtree(person_dir)
            logging.info(f"已删除图片目录: {person_dir}")

            # 2. 从内存中移除该人员的特征
            indices_to_remove = [i for i, person_name in enumerate(self.face_name_known_list) if person_name == name]
            
            # 从后往前删除，避免索引错误
            for i in sorted(indices_to_remove, reverse=True):
                del self.face_name_known_list[i]
                del self.face_feature_known_list[i]

            # 3. 重建 features_all.csv 文件
            self._rebuild_features_csv()
            
            logging.info(f"成功删除人员 '{name}' 并重建了特征文件。")
            return True
        except Exception as e:
            logging.error(f"删除人员 '{name}' 时发生错误: {e}")
            # 如果出错，重新加载数据库以保持一致性
            self.load_face_database()
            return False

    def register_face_capture(self, name, frame):
        """
        为指定姓名的人员捕获并注册一帧中的人脸。
        用于交互式注册流程。
        参数:
            name (str): 正在注册的人员姓名。
            frame (np.ndarray): 从摄像头捕获的视频帧。
        返回:
            dict: 包含操作状态和消息的字典。
        """
        person_dir = os.path.join(FACES_DIR, name)
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
            logging.info(f"为 '{name}' 创建了新的注册目录: {person_dir}")

        # 使用 Dlib 检测器检测人脸
        faces = self.detector(frame, 1)

        if len(faces) == 0:
            return {"status": "error", "message": "未检测到人脸"}
        if len(faces) > 1:
            return {"status": "error", "message": "检测到多张人脸，请确保画面中只有一人"}
        
        face = faces[0]
        # 提取128D特征
        shape = self.predictor(frame, face)
        features = self.face_reco_model.compute_face_descriptor(frame, shape)
        
        # 保存裁剪的人脸图片
        img_num = len(os.listdir(person_dir)) + 1
        img_path = os.path.join(person_dir, f"img_face_{img_num}.jpg")
        
        # 裁剪图片时增加一些边距
        left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
        height, width = bottom - top, right - left
        top = max(0, top - int(height * 0.2))
        bottom = min(frame.shape[0], bottom + int(height * 0.2))
        left = max(0, left - int(width * 0.2))
        right = min(frame.shape[1], right + int(width * 0.2))
        
        cropped_face = frame[top:bottom, left:right]
        cv2.imwrite(img_path, cropped_face)

        # 将新特征追加到 CSV 和内存数据库
        with open(FEATURES_CSV_PATH, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            row_to_write = [name] + list(features)
            writer.writerow(row_to_write)

        self.face_name_known_list.append(name)
        self.face_feature_known_list.append(list(features))

        logging.info(f"为 '{name}' 成功捕获并保存了第 {img_num} 张人脸特征。")
        return {"status": "success", "message": f"成功捕获第 {img_num} 张图片", "count": img_num}

    def _rebuild_features_csv(self):
        """
        使用内存中的特征数据完全重写 features_all.csv 文件。
        """
        with open(FEATURES_CSV_PATH, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for name, features in zip(self.face_name_known_list, self.face_feature_known_list):
                writer.writerow([name] + features)
        logging.info("已成功从内存重建 features_all.csv 文件。")


# 创建一个单例
dlib_face_service = DlibFaceService() 