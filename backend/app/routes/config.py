from flask import Blueprint, request, jsonify
import numpy as np

from app.services.danger_zone import (
    DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD,
    save_danger_zone_config
)

# 创建配置蓝图
config_bp = Blueprint('config', __name__, url_prefix='/api')

# 危险区域编辑模式标志
edit_mode = False

@config_bp.route("/config", methods=["GET"])
def get_config():
    """获取配置信息端点"""
    return jsonify({
        "danger_zone": DANGER_ZONE.tolist(),
        "safety_distance": SAFETY_DISTANCE,
        "loitering_threshold": LOITERING_THRESHOLD
    })

@config_bp.route("/update_danger_zone", methods=["POST"])
def update_danger_zone():
    """更新危险区域坐标端点"""
    global DANGER_ZONE
    data = request.json
    new_zone = data.get('danger_zone')
    
    if new_zone and len(new_zone) >= 3:  # 确保至少有3个点形成多边形
        DANGER_ZONE = np.array(new_zone, np.int32)
        # 保存到配置文件
        if save_danger_zone_config(DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD):
            return jsonify({"status": "success", "message": "Danger zone updated and saved successfully"})
        else:
            return jsonify({"status": "warning", "message": "Danger zone updated but failed to save to file"})
    else:
        return jsonify({"status": "error", "message": "Invalid danger zone coordinates"}), 400

@config_bp.route("/update_thresholds", methods=["POST"])
def update_thresholds():
    """更新安全距离和停留时间阈值端点"""
    global SAFETY_DISTANCE, LOITERING_THRESHOLD
    data = request.json
    
    safety_distance = data.get('safety_distance')
    loitering_threshold = data.get('loitering_threshold')
    
    if safety_distance is not None:
        try:
            SAFETY_DISTANCE = int(safety_distance)
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid safety distance value"}), 400
            
    if loitering_threshold is not None:
        try:
            LOITERING_THRESHOLD = float(loitering_threshold)
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid loitering threshold value"}), 400
    
    # 保存到配置文件
    if save_danger_zone_config(DANGER_ZONE, SAFETY_DISTANCE, LOITERING_THRESHOLD):
        return jsonify({
            "status": "success", 
            "message": "Thresholds updated and saved successfully",
            "safety_distance": SAFETY_DISTANCE,
            "loitering_threshold": LOITERING_THRESHOLD
        })
    else:
        return jsonify({
            "status": "warning", 
            "message": "Thresholds updated but failed to save to file",
            "safety_distance": SAFETY_DISTANCE,
            "loitering_threshold": LOITERING_THRESHOLD
        })

@config_bp.route("/toggle_edit_mode", methods=["POST"])
def toggle_edit_mode():
    """切换危险区域编辑模式端点"""
    global edit_mode
    data = request.json
    edit_mode = data.get('edit_mode', False)
    return jsonify({"status": "success", "edit_mode": edit_mode}) 