# 账套—会计年度表模型（从表，主从关系：会计年度单独分离）
from .base import db


class AccountBookFiscalYear(db.Model):
    """账套—会计年度（从表），与主表 account_book 主从关系，会计年度单独存储"""
    __tablename__ = 'account_book_fiscal_year'
    __table_args__ = {'comment': '账套—会计年度（从表），主从关系'}

    account_book_code = db.Column(db.String(50), db.ForeignKey('account_book.account_book_code', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, comment='账套编码')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='首次导入该年度的时间')
