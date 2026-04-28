# 自定义档案项表模型（按账套+年度，对应 Share.json 自定义档案项定义，依赖 account_book_fiscal_year）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class CustomArchiveItem(db.Model):
    """自定义档案项表，按账套+年度，同一账套同一年度下档案编码唯一；依赖 account_book_fiscal_year"""
    __tablename__ = 'custom_archive_item'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '自定义档案项表(定义)，按账套+年度，对应 Share.json 自定义档案项'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    archive_item_code = db.Column(db.String(50), primary_key=True, comment='档案编码，对应 Share.json 档案编码，如 ACC_ITEM1、B_ACC_CODE')
    archive_item_name = db.Column(db.String(200), nullable=False, comment='档案名称，对应 Share.json 档案名称')
    archive_item_desc = db.Column(db.String(500), comment='档案描述，对应 Share.json 档案描述')
    has_hierarchy = db.Column(db.SmallInteger, nullable=False, default=1, comment='是否有层级特征：1=是 0=否')
    archive_code_rule = db.Column(db.String(50), comment='档案编码规则，如 4-2-2-2、3-3-2')
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
            'archive_item_name': self.archive_item_name,
            'archive_item_desc': self.archive_item_desc,
            'has_hierarchy': self.has_hierarchy,
            'archive_code_rule': self.archive_code_rule,
            'remark': self.remark,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
