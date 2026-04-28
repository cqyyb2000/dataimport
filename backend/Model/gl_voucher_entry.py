# 记账凭证分录行表模型（对应 GL.xml 记账凭证分录行，按账套+年度+期间+凭证编号+分录行号）
from sqlalchemy import ForeignKeyConstraint, DECIMAL

from .base import db


class GLVoucherEntry(db.Model):
    """记账凭证分录行表，对应 GL.xml 记账凭证分录行，按账套+年度+期间+凭证编号+分录行号"""
    __tablename__ = 'gl_voucher_entry'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year', 'period_number', 'voucher_number'],
            ['gl_voucher.account_book_code', 'gl_voucher.fiscal_year', 'gl_voucher.period_number', 'gl_voucher.voucher_number'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '记账凭证分录行表，对应 GL.xml 记账凭证分录行，按账套+年度+期间+凭证编号+分录行号'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    period_number = db.Column(db.SmallInteger, primary_key=True, comment='会计期间号，1-12或13')
    voucher_number = db.Column(db.String(50), primary_key=True, comment='凭证编号，外键关联 gl_voucher，对应 XML 凭证编号')
    entry_line_number = db.Column(db.Integer, primary_key=True, comment='分录行号，对应 XML 分录行号')
    account_code = db.Column(db.String(50), nullable=False, comment='科目编号，对应 XML 科目编号')
    summary = db.Column(db.String(500), comment='分录摘要，对应 XML 摘要')
    debit_amount = db.Column(DECIMAL(18, 2), comment='借方金额，对应 XML 借方金额')
    credit_amount = db.Column(DECIMAL(18, 2), comment='贷方金额，对应 XML 贷方金额')
    currency_code = db.Column(db.String(10), comment='币种编码，对应 XML 币种编码')
    exchange_rate = db.Column(DECIMAL(18, 6), comment='汇率，对应 XML 汇率')
    original_currency_debit_amount = db.Column(DECIMAL(18, 2), comment='原币借方金额，对应 XML 原币借方金额')
    original_currency_credit_amount = db.Column(DECIMAL(18, 2), comment='原币贷方金额，对应 XML 原币贷方金额')
    quantity = db.Column(DECIMAL(18, 4), comment='数量，对应 XML 数量')
    unit_price = db.Column(DECIMAL(18, 4), comment='单价，对应 XML 单价')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'period_number': self.period_number,
            'voucher_number': self.voucher_number,
            'entry_line_number': self.entry_line_number,
            'account_code': self.account_code,
            'summary': self.summary,
            'debit_amount': float(self.debit_amount) if self.debit_amount is not None else None,
            'credit_amount': float(self.credit_amount) if self.credit_amount is not None else None,
            'currency_code': self.currency_code,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate is not None else None,
            'original_currency_debit_amount': float(self.original_currency_debit_amount) if self.original_currency_debit_amount is not None else None,
            'original_currency_credit_amount': float(self.original_currency_credit_amount) if self.original_currency_credit_amount is not None else None,
            'quantity': float(self.quantity) if self.quantity is not None else None,
            'unit_price': float(self.unit_price) if self.unit_price is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
