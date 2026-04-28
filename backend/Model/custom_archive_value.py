# 自定义档案值表模型（按账套+年度，对应 Share.json 自定义档案值数据，依赖 custom_archive_item）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class CustomArchiveValue(db.Model):
    """自定义档案值表，按账套+年度，同一档案项下档案值编码唯一；依赖 custom_archive_item"""
    __tablename__ = 'custom_archive_value'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year', 'archive_item_code'],
            ['custom_archive_item.account_book_code', 'custom_archive_item.fiscal_year', 'custom_archive_item.archive_item_code'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '自定义档案值表(数据)，按账套+年度，对应 Share.json 自定义档案值'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    archive_item_code = db.Column(db.String(50), primary_key=True, comment='档案编码，关联 custom_archive_item')
    archive_value_code = db.Column(db.String(50), primary_key=True, comment='档案值编码，如 0001、000101')
    archive_value_name = db.Column(db.String(200), nullable=False, comment='档案值名称')
    archive_value_desc = db.Column(db.String(500), comment='档案值描述')
    parent_value_code = db.Column(db.String(50), comment='档案值父节点，空表示根节点')
    level = db.Column(db.SmallInteger, nullable=False, comment='档案值级次，如 1、2')
    remark = db.Column(db.String(500), comment='备注')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1=启用 0=停用')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'archive_item_code': self.archive_item_code,
            'archive_value_code': self.archive_value_code,
            'archive_value_name': self.archive_value_name,
            'archive_value_desc': self.archive_value_desc,
            'parent_value_code': self.parent_value_code,
            'level': self.level,
            'remark': self.remark,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
