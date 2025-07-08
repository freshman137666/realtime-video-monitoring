from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """创建并配置Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 初始化数据库和迁移工具
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册API蓝图
    # Flask-RESTX的Api对象会自动处理URL前缀，所以这里不需要指定
    from .api import api_bp
    app.register_blueprint(api_bp)

    return app 