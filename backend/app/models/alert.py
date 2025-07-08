from datetime import datetime
from app import db

class Alert(db.Model):
    """报警信息模型"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # 报警类型，如"入侵"、"靠近危险区域"等
    description = db.Column(db.String(200))  # 报警描述
    image_path = db.Column(db.String(200))  # 报警截图路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 报警时间
    is_handled = db.Column(db.Boolean, default=False)  # 是否已处理
    
    def __repr__(self):
        return f'<Alert {self.id}: {self.alert_type}>'
    
    def to_dict(self):
        """将模型转换为字典，便于API返回JSON"""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'description': self.description,
            'image_path': self.image_path,
            'created_at': self.created_at.isoformat(),
            'is_handled': self.is_handled
        } 