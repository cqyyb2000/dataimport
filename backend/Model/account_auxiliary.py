# 科目辅助核算表模型（按账套+年度，对应 SHARE.xml 科目辅助核算，依赖 account）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class AccountAuxiliary(db.Model):
    """科目辅助核算表，按账套+年度，同一账套同一年度下科目编号+辅助项编号唯一；依赖 account"""
    __tablename__ = 'account_auxiliary'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year', 'account_code'],
            ['account.account_book_code', 'account.fiscal_year', 'account.account_code'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '科目辅助核算表(account_auxiliary)，按账套+年度，对应 SHARE.xml 科目辅助核算'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    account_code = db.Column(db.String(50), primary_key=True, comment='科目编号，外键关联 account，对应 SHARE.xml 科目编号')
    auxiliary_item_code = db.Column(db.String(50), primary_key=True, comment='辅助项编号，对应 SHARE.xml 辅助项编号')
    auxiliary_item_name = db.Column(db.String(200), nullable=False, comment='辅助项名称，对应 SHARE.xml 辅助项名称')
    corresponding_archive = db.Column(db.String(200), comment='对应档案，对应 SHARE.xml 对应档案')
    auxiliary_item_description = db.Column(db.String(500), comment='辅助项描述，对应 SHARE.xml 辅助项描述')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1=启用 0=停用')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'account_code': self.account_code,
            'auxiliary_item_code': self.auxiliary_item_code,
            'auxiliary_item_name': self.auxiliary_item_name,
            'corresponding_archive': self.corresponding_archive,
            'auxiliary_item_description': self.auxiliary_item_description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
