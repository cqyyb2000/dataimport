# 菜单表模型
from .base import db


class Menu(db.Model):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    component = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, default=0)
    path = db.Column(db.String(100))
    icon = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)
