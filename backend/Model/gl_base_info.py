# 总账基础信息表模型（对应 GL.xml 总账基础信息，按账套+年度）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class GLBaseInfo(db.Model):
    """总账基础信息表，对应 GL.xml 总账基础信息，按账套+年度"""
    __tablename__ = 'gl_base_info'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '总账基础信息表，对应 GL.xml 总账基础信息，按账套+年度'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    structure_separator = db.Column(db.String(1), comment='结构分隔符，科目编号的分隔符，对应 XML 结构分隔符')
    account_code_rule = db.Column(db.String(50), comment='会计科目编号规则，对应 XML 会计科目编号规则')
    voucher_header_ext_fields = db.Column(db.String(500), comment='凭证头可扩展字段结构，对应 XML 凭证头可扩展字段结构')
    voucher_header_ext_archives = db.Column(db.String(500), comment='凭证头可扩展结构对应档案，对应 XML 凭证头可扩展结构对应档案')
    entry_line_ext_fields = db.Column(db.String(500), comment='分录行可扩展字段结构，对应 XML 分录行可扩展字段结构')
    entry_line_ext_archives = db.Column(db.String(500), comment='分录行可扩展字段对应档案，对应 XML 分录行可扩展字段对应档案')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'structure_separator': self.structure_separator,
            'account_code_rule': self.account_code_rule,
            'voucher_header_ext_fields': self.voucher_header_ext_fields,
            'voucher_header_ext_archives': self.voucher_header_ext_archives,
            'entry_line_ext_fields': self.entry_line_ext_fields,
            'entry_line_ext_archives': self.entry_line_ext_archives,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
