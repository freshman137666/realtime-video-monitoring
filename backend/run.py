from app import create_app, db
from ultralytics import YOLO

# 从应用工厂创建Flask应用实例
app = create_app()

# 加载YOLOv8模型 (可以放在这里全局加载，也可以在需要时再加载)
# 注意：确保你的 `yolov8n.pt` 文件在 `backend` 目录下
try:
    yolo_model = YOLO('yolov8n.pt')
    print("YOLOv8 model loaded successfully.")
except Exception as e:
    print(f"Error loading YOLOv8 model: {e}")
    yolo_model = None

@app.shell_context_processor
def make_shell_context():
    """为 'flask shell' 命令添加上下文"""
    return {'db': db}

if __name__ == '__main__':
    # 启动应用
    # 注意：debug=True 模式在生产环境中不应使用
    app.run(host='0.0.0.0', port=5000, debug=True) 