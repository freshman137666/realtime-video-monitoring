from flask import Blueprint, jsonify

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route("/status", methods=["GET"])
def api_status():
    """API状态检查端点"""
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "message": "Video monitoring API is operational"
    })

@api_bp.route("/alerts")
def get_alerts():
    """获取告警信息端点"""
    from app.services.alerts import get_alerts
    return jsonify({"alerts": get_alerts()}) 