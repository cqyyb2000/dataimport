# 记账凭证表模型（对应 GL.xml 记账凭证，按账套+年度+期间+凭证编号）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class GLVoucher(db.Model):
    """记账凭证表，对应 GL.xml 记账凭证，按账套+年度+期间+凭证编号"""
    __tablename__ = 'gl_voucher'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year', 'voucher_type_code'],
            ['gl_voucher_type.account_book_code', 'gl_voucher_type.fiscal_year', 'gl_voucher_type.voucher_type_code'],
            ondelete='RESTRICT',
            onupdate='CASCADE',
        ),
        {'comment': '记账凭证表，对应 GL.xml 记账凭证，按账套+年度+期间+凭证编号'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021，对应 XML 会计年度')
    period_number = db.Column(db.SmallInteger, primary_key=True, comment='会计期间号，1-12或13，对应 XML 会计期间号')
    voucher_number = db.Column(db.String(50), primary_key=True, comment='凭证编号，对应 XML 凭证编号')
    voucher_date = db.Column(db.String(8), nullable=False, comment='凭证日期，格式 YYYYMMDD，对应 XML 凭证日期')
    voucher_type_code = db.Column(db.String(50), nullable=False, comment='记账凭证类型编号，外键关联 gl_voucher_type，对应 XML 记账凭证类型编号')
    attachment_count = db.Column(db.Integer, comment='附单据数，对应 XML 附单据数')
    prepared_by = db.Column(db.String(50), comment='制单人，对应 XML 制单人')
    reviewed_by = db.Column(db.String(50), comment='审核人，对应 XML 审核人')
    posted_by = db.Column(db.String(50), comment='记账人，对应 XML 记账人')
    voucher_status = db.Column(db.String(20), comment='凭证状态，对应 XML 凭证状态')
    summary = db.Column(db.String(500), comment='凭证摘要，对应 XML 摘要')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 关联关系：一个凭证可以有多个分录行
    entries = db.relationship('GLVoucherEntry', backref='voucher', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'period_number': self.period_number,
            'voucher_number': self.voucher_number,
            'voucher_date': self.voucher_date,
            'voucher_type_code': self.voucher_type_code,
            'attachment_count': self.attachment_count,
            'prepared_by': self.prepared_by,
            'reviewed_by': self.reviewed_by,
            'posted_by': self.posted_by,
            'voucher_status': self.voucher_status,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
