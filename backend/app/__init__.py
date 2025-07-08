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

    # 在这里可以注册蓝图
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app 