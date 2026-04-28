# 科目余额表模型（对应 GL.xml 科目余额，按账套+年度+期间+科目+币种）
from sqlalchemy import ForeignKeyConstraint, DECIMAL

from .base import db


class GLAccountBalance(db.Model):
    """科目余额表，对应 GL.xml 科目余额，按账套+年度+期间+科目+币种"""
    __tablename__ = 'gl_account_balance'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '科目余额表，对应 GL.xml 科目余额，按账套+年度+期间+科目+币种'},
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='自增主键')
    account_book_code = db.Column(db.String(50), nullable=False, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, nullable=False, comment='会计年度，4位如2021，对应 XML 会计年度')
    period_number = db.Column(db.SmallInteger, nullable=False, comment='会计期间号，0表示期初，1-12表示各期间，对应 XML 会计期间号')
    account_code = db.Column(db.String(50), nullable=False, comment='科目编号，对应 XML 科目编号')
    opening_balance = db.Column(DECIMAL(18, 2), comment='期初余额，对应 XML 期初余额')
    opening_balance_direction = db.Column(db.String(10), comment='期初余额方向，借/贷，对应 XML 期初余额方向')
    current_period_debit_amount = db.Column(DECIMAL(18, 2), comment='本期借方发生额，对应 XML 本期借方发生额')
    current_period_credit_amount = db.Column(DECIMAL(18, 2), comment='本期贷方发生额，对应 XML 本期贷方发生额')
    closing_balance = db.Column(DECIMAL(18, 2), comment='期末余额，对应 XML 期末余额')
    closing_balance_direction = db.Column(db.String(10), comment='期末余额方向，借/贷，对应 XML 期末余额方向')
    currency_code = db.Column(db.String(10), comment='币种编码，对应 XML 币种编码')
    # 库中列名为 ParentCode（与部分 XML/科目表一致）
    parent_code = db.Column('ParentCode', db.String(50), comment='父级科目编号')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'id': self.id,
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'period_number': self.period_number,
            'account_code': self.account_code,
            'opening_balance': float(self.opening_balance) if self.opening_balance is not None else None,
            'opening_balance_direction': self.opening_balance_direction,
            'current_period_debit_amount': float(self.current_period_debit_amount) if self.current_period_debit_amount is not None else None,
            'current_period_credit_amount': float(self.current_period_credit_amount) if self.current_period_credit_amount is not None else None,
            'closing_balance': float(self.closing_balance) if self.closing_balance is not None else None,
            'closing_balance_direction': self.closing_balance_direction,
            'currency_code': self.currency_code,
            'parent_code': self.parent_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
