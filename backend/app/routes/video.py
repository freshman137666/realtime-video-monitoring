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
    """视频流端点
    ---
    tags:
      - 视频处理
    description: >
      提供实时视频流。
      此端点返回一个 multipart/x-mixed-replace 响应，用于视频流。
      浏览器中的 `<img>` 标签可以直接使用此端点的URL作为 `src`。
    produces:
      - multipart/x-mixed-replace; boundary=frame
    responses:
      200:
        description: 视频流正在传输.
    """
    return video_feed()

@video_bp.route('/upload', methods=['POST'])
def upload_file():
    """文件上传处理端点
    ---
    tags:
      - 视频处理
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: 要上传的视频 (mp4) 或图片 (jpg) 文件.
    responses:
      200:
        description: 文件处理成功.
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            media_type:
              type: string
              example: video
            file_url:
              type: string
              description: 处理后可供访问的文件URL.
              example: /api/files/processed_video.mp4
            alerts:
              type: array
              items:
                type: string
              description: 处理过程中生成的警报列表.
      400:
        description: 请求错误，例如没有文件、文件类型不支持等.
    """
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
    """文件访问端点
    ---
    tags:
      - 视频处理
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: 要访问的文件名 (通常是处理后的视频或图片).
    responses:
      200:
        description: 成功返回文件.
      404:
        description: 文件未找到.
    """
    print(f"请求访问文件: {filename}, 目录: {UPLOADS_DIR}")
    # 确保安全的文件名访问
    filename = secure_filename(filename)
    return send_from_directory(UPLOADS_DIR, filename) 