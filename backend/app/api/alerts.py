from flask import request
from flask_restx import Namespace, Resource, fields
from app import db
from app.models import Alert

# 创建报警API的命名空间
ns = Namespace('alerts', description='报警相关操作')

# 定义报警模型，用于Swagger文档
alert_model = ns.model('Alert', {
    'id': fields.Integer(readonly=True, description='报警ID'),
    'alert_type': fields.String(required=True, description='报警类型'),
    'description': fields.String(description='报警描述'),
    'image_path': fields.String(description='报警截图路径'),
    'created_at': fields.DateTime(description='报警时间'),
    'is_handled': fields.Boolean(description='是否已处理')
})

# 定义创建报警的输入模型
alert_input = ns.model('AlertInput', {
    'alert_type': fields.String(required=True, description='报警类型'),
    'description': fields.String(description='报警描述'),
    'image_path': fields.String(description='报警截图路径')
})

@ns.route('/')
class AlertList(Resource):
    @ns.doc('list_alerts')
    @ns.marshal_list_with(alert_model)
    def get(self):
        """获取所有报警"""
        alerts = Alert.query.order_by(Alert.created_at.desc()).all()
        return alerts
    
    @ns.doc('create_alert')
    @ns.expect(alert_input)
    @ns.marshal_with(alert_model, code=201)
    def post(self):
        """创建新报警"""
        data = request.json
        alert = Alert(
            alert_type=data['alert_type'],
            description=data.get('description', ''),
            image_path=data.get('image_path', '')
        )
        db.session.add(alert)
        db.session.commit()
        return alert, 201

@ns.route('/<int:id>')
@ns.response(404, '报警不存在')
@ns.param('id', '报警ID')
class AlertItem(Resource):
    @ns.doc('get_alert')
    @ns.marshal_with(alert_model)
    def get(self, id):
        """获取指定ID的报警"""
        alert = Alert.query.get_or_404(id)
        return alert
    
    @ns.doc('update_alert')
    @ns.expect(alert_model)
    @ns.marshal_with(alert_model)
    def put(self, id):
        """更新报警信息"""
        alert = Alert.query.get_or_404(id)
        data = request.json
        
        if 'alert_type' in data:
            alert.alert_type = data['alert_type']
        if 'description' in data:
            alert.description = data['description']
        if 'image_path' in data:
            alert.image_path = data['image_path']
        if 'is_handled' in data:
            alert.is_handled = data['is_handled']
            
        db.session.commit()
        return alert
    
    @ns.doc('delete_alert')
    @ns.response(204, '报警已删除')
    def delete(self, id):
        """删除报警"""
        alert = Alert.query.get_or_404(id)
        db.session.delete(alert)
        db.session.commit()
        return '', 204

@ns.route('/handle/<int:id>')
@ns.response(404, '报警不存在')
@ns.param('id', '报警ID')
class AlertHandle(Resource):
    @ns.doc('handle_alert')
    @ns.marshal_with(alert_model)
    def put(self, id):
        """标记报警为已处理"""
        alert = Alert.query.get_or_404(id)
        alert.is_handled = True
        db.session.commit()
        return alert 