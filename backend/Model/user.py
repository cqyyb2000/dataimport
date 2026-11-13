# 用户表模型
from .base import db


class User(db.Model):
    ROLE_ACCOUNTANT = 'accountant'
    ROLE_CASHIER = 'cashier'

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), comment='报销台账角色：accountant=会计，cashier=出纳；管理员可为空')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'role': self.role,
        }
