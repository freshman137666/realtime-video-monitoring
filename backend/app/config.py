import os

# 获取项目根目录的绝对路径
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-very-secure'

    # MySQL 数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DB = 'realtime_monitoring'
    MYSQL_CHARSET = 'utf8mb4'

    # SQLAlchemy 配置 - 使用 MySQL
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset={MYSQL_CHARSET}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False