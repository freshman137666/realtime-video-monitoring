from collections import defaultdict
import time

# 用于跟踪目标在危险区域内的停留时间
target_loitering_time = defaultdict(float)

# 上次检测的时间戳
last_detection_time = time.time()

# 用于存储告警信息
alerts = []

def reset_alerts():
    """重置所有警报信息"""
    global alerts, target_loitering_time, last_detection_time
    alerts = []
    target_loitering_time = defaultdict(float)
    last_detection_time = time.time()

def add_alert(alert_message):
    """添加新的警报信息"""
    global alerts
    if alert_message not in alerts:
        alerts.append(alert_message)
        print(f"Alert: {alert_message}")

def get_alerts():
    """获取当前所有警报信息"""
    return alerts

def update_loitering_time(target_id, time_diff):
    """更新目标在危险区域的停留时间"""
    global target_loitering_time
    target_loitering_time[target_id] += time_diff
    return target_loitering_time[target_id]

def reset_loitering_time(target_id):
    """重置目标的停留时间"""
    global target_loitering_time
    target_loitering_time[target_id] = 0

def get_loitering_time(target_id):
    """获取目标的停留时间"""
    return target_loitering_time[target_id]

def update_detection_time():
    """更新检测时间并返回时间差"""
    global last_detection_time
    current_time = time.time()
    time_diff = current_time - last_detection_time
    last_detection_time = current_time
    return time_diff 