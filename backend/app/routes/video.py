import os
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from app.services.detection import process_image, process_video
from app.services.video import video_feed
from app.services.alerts import reset_alerts

# 创建视频蓝图
video_bp = Blueprint('video', __name__, url_prefix='/api')

# 定义上传目录路径
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

@video_bp.route('/video_feed')
def get_video_feed():
    """视频流端点"""
    return video_feed()

@video_bp.route('/upload', methods=['POST'])
def upload_file():
    """文件上传处理端点"""
    # 重置警报
    reset_alerts()
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOADS_DIR, filename)
        file.save(filepath)
        
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_extension == 'jpg':
            # 处理图片上传
            return jsonify(process_image(filepath, UPLOADS_DIR))
        elif file_extension == 'mp4':
            # 处理视频上传
            return jsonify(process_video(filepath, UPLOADS_DIR))
        else:
            return jsonify({
                "status": "error", 
                "message": "Unsupported file type. Please upload JPG or MP4."
            }), 400

@video_bp.route('/files/<filename>')
def serve_file(filename):
    """文件访问端点"""
    print(f"请求访问文件: {filename}, 目录: {UPLOADS_DIR}")
    # 确保安全的文件名访问
    filename = secure_filename(filename)
    return send_from_directory(UPLOADS_DIR, filename) 