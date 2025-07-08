from flask import Blueprint
from flask_restx import Api

# 创建API蓝图实例，并直接指定URL前缀
# 这样所有与此蓝图相关的URL都会自动以/api开头
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 创建一个Api对象，并将其绑定到蓝图上
# 这是我们与Swagger/flask-restx交互的核心
api = Api(api_bp,
          version='1.0',
          title='Realtime Video Monitoring API',
          description='A comprehensive API for real-time video analysis and monitoring.',
          doc='/',  # 这会将Swagger UI的访问路径设置为蓝图的根，即 /api/
          )

# 在这里导入各个模块的命名空间
# flask-restx会自动处理路径拼接，例如：/api/alerts
from .alerts import ns as alerts_ns
api.add_namespace(alerts_ns, path='/alerts')

from .video import ns as video_ns
api.add_namespace(video_ns, path='/video')

from .face import ns as face_ns
api.add_namespace(face_ns, path='/face')

# from .config import ns as config_ns
# api.add_namespace(config_ns) 