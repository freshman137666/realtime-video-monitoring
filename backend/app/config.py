import os

# 获取项目根目录的绝对路径
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'
    
    # SQLAlchemy 配置
    # 使用SQLite作为开发数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False 

     # 数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Really0733251'
    MYSQL_DB = 'realtime_monitoring'
    MYSQL_CHARSET = 'utf8mb4'