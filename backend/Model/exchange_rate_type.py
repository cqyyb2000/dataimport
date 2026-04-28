# 汇率类型表模型（按账套+年度，对应 Share.json 汇率类型，依赖 account_book_fiscal_year）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class ExchangeRateType(db.Model):
    """汇率类型表，按账套+年度，同一账套同一年度下汇率类型编号唯一；依赖 account_book_fiscal_year"""
    __tablename__ = 'exchange_rate_type'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '汇率类型表，按账套+年度，对应 Share.json 汇率类型'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    exchange_rate_type_code = db.Column(db.String(10), primary_key=True, comment='汇率类型编号，对应 Share.json 汇率类型编号')
    exchange_rate_type_name = db.Column(db.String(100), nullable=False, comment='汇率类型名称，对应 Share.json 汇率类型名称')
    remark = db.Column(db.String(500), comment='备注')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1=启用 0=停用')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'exchange_rate_type_code': self.exchange_rate_type_code,
            'exchange_rate_type_name': self.exchange_rate_type_name,
            'remark': self.remark,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
