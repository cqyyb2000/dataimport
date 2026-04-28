# 会计科目表模型（按账套+年度，对应 SHARE.xml 会计科目，依赖 account_book_fiscal_year）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class Account(db.Model):
    """会计科目表，按账套+年度，同一账套同一年度下科目编号唯一；依赖 account_book_fiscal_year"""
    __tablename__ = 'account'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year', 'parent_account_code'],
            ['account.account_book_code', 'account.fiscal_year', 'account.account_code'],
            ondelete='RESTRICT',
            onupdate='CASCADE',
        ),
        {'comment': '会计科目表(account)，按账套+年度，对应 SHARE.xml 会计科目'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    account_code = db.Column(db.String(50), primary_key=True, comment='科目编号，对应 SHARE.xml 科目编号')
    account_name = db.Column(db.String(200), nullable=False, comment='科目名称，对应 SHARE.xml 科目名称')
    account_level = db.Column(db.SmallInteger, nullable=False, comment='科目级次，对应 SHARE.xml 科目级次，如 1、2')
    account_type = db.Column(db.String(50), nullable=False, comment='科目类型，对应 SHARE.xml 科目类型：资产类/负债类/净资产类/收入类/支出类')
    balance_direction = db.Column(db.String(10), nullable=False, comment='余额方向，对应 SHARE.xml 余额方向：借/贷')
    is_leaf = db.Column(db.SmallInteger, default=0, comment='是否末级，对应 SHARE.xml 是否末级：1=是 0=否')
    is_enabled = db.Column(db.SmallInteger, default=1, comment='是否启用，对应 SHARE.xml 是否启用：1=启用 0=停用')
    parent_account_code = db.Column(db.String(50), comment='上级科目编号，对应 SHARE.xml 上级科目编号')
    remark = db.Column(db.String(500), comment='备注')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1=启用 0=停用')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 关联关系：一个科目可以有多个辅助核算项
    auxiliary_items = db.relationship('AccountAuxiliary', backref='account', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'account_code': self.account_code,
            'account_name': self.account_name,
            'account_level': self.account_level,
            'account_type': self.account_type,
            'balance_direction': self.balance_direction,
            'is_leaf': self.is_leaf,
            'is_enabled': self.is_enabled,
            'parent_account_code': self.parent_account_code,
            'remark': self.remark,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
