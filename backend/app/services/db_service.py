import mysql.connector
from app.config import Config

def init_database():
    """初始化数据库和表结构"""
    try:
        # 创建数据库连接
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB} DEFAULT CHARSET {Config.MYSQL_CHARSET}")
        cursor.execute(f"USE {Config.MYSQL_DB}")
        
        # 创建乘客表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS passengers (
             passenger_id VARCHAR(36) NOT NULL PRIMARY KEY COMMENT '乘客唯一标识符(UUID)',
            id_card_number VARCHAR(18) UNIQUE COMMENT '身份证号码',
            name VARCHAR(50) NOT NULL COMMENT '乘客姓名',
            gender CHAR(1) COMMENT '性别(M-男, F-女)',
            registered_face_feature JSON COMMENT '人脸特征向量(JSON格式)',
            registration_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
             blacklist_flag BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否在黑名单中',
             blacklist_reason TEXT COMMENT '加入黑名单的原因',
             last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # 创建人脸识别记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_recognition_logs (
            recognition_id VARCHAR(36) NOT NULL PRIMARY KEY COMMENT '识别记录ID(UUID)',
            passenger_id VARCHAR(36) COMMENT '匹配到的乘客ID',
            recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '识别时间',
            FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        print("✅ 数据库表创建成功!")
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ 数据库初始化失败: {err}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()