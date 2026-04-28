# 权限表模型
from .base import db


class Permission(db.Model):
    __tablename__ = 'permissions'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), primary_key=True)
