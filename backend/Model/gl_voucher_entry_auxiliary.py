# -*- coding: utf-8 -*-
"""
凭证分录辅助项明细表模型（记录有辅助项的分录的辅助核算明细）
对应 gl_voucher_entry_auxiliary 表，关联 gl_voucher_entry
"""
from sqlalchemy import ForeignKeyConstraint

from .base import db


class GLVoucherEntryAuxiliary(db.Model):
    """凭证分录辅助项明细表，对应 GL.xml 辅助项1编号~辅助项30编号"""
    __tablename__ = 'gl_voucher_entry_auxiliary'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year', 'period_number', 'voucher_number', 'entry_line_number'],
            ['gl_voucher_entry.account_book_code', 'gl_voucher_entry.fiscal_year', 'gl_voucher_entry.period_number',
             'gl_voucher_entry.voucher_number', 'gl_voucher_entry.entry_line_number'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '凭证分录辅助项明细表，记录有辅助项的分录的辅助核算明细'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度')
    period_number = db.Column(db.SmallInteger, primary_key=True, comment='会计期间号')
    voucher_number = db.Column(db.String(50), primary_key=True, comment='凭证编号')
    entry_line_number = db.Column(db.Integer, primary_key=True, comment='分录行号')
    auxiliary_item_sequence = db.Column(db.SmallInteger, primary_key=True, comment='辅助项序号，1-30')
    account_code = db.Column(db.String(50), nullable=False, comment='科目编号')
    auxiliary_value = db.Column(db.String(50), nullable=False, comment='辅助项取值')
    auxiliary_item_name = db.Column(db.String(100), comment='辅助项名称，来自 account_auxiliary')
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
            'auxiliary_item_sequence': self.auxiliary_item_sequence,
            'account_code': self.account_code,
            'auxiliary_value': self.auxiliary_value,
            'auxiliary_item_name': self.auxiliary_item_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
