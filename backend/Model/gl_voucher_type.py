# 记账凭证类型表模型（对应 GL.xml 记账凭证类型，按账套+年度）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class GLVoucherType(db.Model):
    """记账凭证类型表，对应 GL.xml 记账凭证类型，按账套+年度"""
    __tablename__ = 'gl_voucher_type'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '记账凭证类型表，对应 GL.xml 记账凭证类型，按账套+年度'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    voucher_type_code = db.Column(db.String(50), primary_key=True, comment='记账凭证类型编号，对应 XML 记账凭证类型编号')
    voucher_type_name = db.Column(db.String(200), nullable=False, comment='记账凭证类型名称，对应 XML 记账凭证类型名称')
    voucher_type_abbreviation = db.Column(db.String(50), comment='记账凭证类型简称，对应 XML 记账凭证类型简称')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 关联关系：一个凭证类型可以有多个凭证
    vouchers = db.relationship('GLVoucher', backref='voucher_type', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'voucher_type_code': self.voucher_type_code,
            'voucher_type_name': self.voucher_type_name,
            'voucher_type_abbreviation': self.voucher_type_abbreviation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
