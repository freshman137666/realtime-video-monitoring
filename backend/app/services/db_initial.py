import mysql.connector
from app.config import Config
import uuid

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
        
        # 创建车站信息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            station_id VARCHAR(36) NOT NULL PRIMARY KEY COMMENT '车站ID(UUID)',
            station_name VARCHAR(100) NOT NULL COMMENT '车站名称',
            city VARCHAR(50) NOT NULL COMMENT '所在城市',
            address TEXT COMMENT '详细地址',
            contact_number VARCHAR(20) COMMENT '车站联系电话'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 创建车站位置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            location_id VARCHAR(36) NOT NULL PRIMARY KEY COMMENT '位置ID(UUID)',
            location_name VARCHAR(100) NOT NULL COMMENT '位置名称',
            location_type VARCHAR(50) NOT NULL COMMENT '位置类型(entrance/security_check/waiting_hall/platform)',
            station_id VARCHAR(36) NOT NULL COMMENT '所属车站ID',
            floor_number INT COMMENT '楼层号',
            coordinates VARCHAR(100) COMMENT '坐标信息(GPS或室内坐标)',
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 创建摄像头设备表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            camera_id VARCHAR(36) NOT NULL PRIMARY KEY COMMENT '摄像头ID(UUID)',
            location_id VARCHAR(36) NOT NULL COMMENT '安装位置ID',
            camera_type VARCHAR(50) NOT NULL COMMENT '摄像头类型(face_recognition/behavior_monitoring)',
            model_number VARCHAR(50) COMMENT '设备型号',
            ip_address VARCHAR(50) COMMENT 'IP地址',
            installation_date DATE COMMENT '安装日期',
            last_maintenance_date DATE COMMENT '最后维护日期',
            status VARCHAR(20) DEFAULT 'active' COMMENT '设备状态(active/inactive/maintenance)',
            FOREIGN KEY (location_id) REFERENCES locations(location_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

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

       # 新增用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(36) NOT NULL PRIMARY KEY COMMENT '用户唯一标识符(UUID)',
            username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
            password VARCHAR(100) NOT NULL COMMENT '密码哈希',
            email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            last_login TIMESTAMP NULL COMMENT '最后登录时间',
            is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '账户是否激活'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
        """)

        print("✅ 数据库表创建成功!")
       
        check_query = "SELECT COUNT(*) FROM users WHERE username = 'admin@qq.co'"
        cursor.execute(check_query)
        count = cursor.fetchone()[0]

        if count == 0:
            # 生成UUID作为user_id
            admin_user_id = str(uuid.uuid4())
            
            insert_query = """
            INSERT INTO users (
                user_id, username, password, email, created_at, last_login, is_active
            ) VALUES (
                %s, 'admin@qq.com', '123', 'admin@qq.com', 
                '2025-07-11 11:39:32', '2025-07-11 03:40:23', 1
            )
            """
            cursor.execute(insert_query, (admin_user_id,))
            conn.commit()
            print(f"✅ 管理员用户插入成功 (ID: {admin_user_id})")
        else:
            print("ℹ️ 管理员用户已存在，跳过插入")

        return True


        
    except mysql.connector.Error as err:
        print(f"❌ 数据库初始化失败: {err}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()