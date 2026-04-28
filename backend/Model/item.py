# 项目表模型（按账套+年度，对应 Share.json 项目，依赖 account_book_fiscal_year）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class Item(db.Model):
    """项目表，按账套+年度，同一账套同一年度下项目编码唯一；依赖 account_book_fiscal_year"""
    __tablename__ = 'item'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '项目表(item)，按账套+年度，对应 Share.json 项目'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    item_code = db.Column(db.String(50), primary_key=True, comment='项目编码，对应 Share.json 项目编码')
    item_name = db.Column(db.String(200), nullable=False, comment='项目名称，对应 Share.json 项目名称')
    level = db.Column(db.SmallInteger, nullable=False, comment='级次，对应 Share.json 级次，如 1、2')
    item_type = db.Column(db.String(50), comment='项目类型，对应 Share.json 项目类型')
    item_category = db.Column(db.String(50), comment='项目类别，对应 Share.json 项目类别')
    item_attribute = db.Column(db.String(50), comment='项目属性，对应 Share.json 项目属性')
    item_start_date = db.Column(db.String(8), comment='项目起始日期，格式 YYYYMMDD，00000000 表示无')
    item_end_date = db.Column(db.String(8), comment='项目结束日期，格式 YYYYMMDD，00000000 表示无')
    remark = db.Column(db.String(500), comment='备注')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1=启用 0=停用')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'level': self.level,
            'item_type': self.item_type,
            'item_category': self.item_category,
            'item_attribute': self.item_attribute,
            'item_start_date': self.item_start_date,
            'item_end_date': self.item_end_date,
            'remark': self.remark,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
