# 内设机构表模型（按账套+年度，对应 XML 内设机构，依赖 account_book_fiscal_year）
from sqlalchemy import ForeignKeyConstraint

from .base import db


class InternalOrganization(db.Model):
    """内设机构表，按账套+年度，同一账套同一年度下内设机构编码唯一；依赖 account_book_fiscal_year"""
    __tablename__ = 'internal_organization'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_book_code', 'fiscal_year'],
            ['account_book_fiscal_year.account_book_code', 'account_book_fiscal_year.fiscal_year'],
            ondelete='CASCADE',
            onupdate='CASCADE',
        ),
        {'comment': '内设机构表，按账套+年度，对应 XML 内设机构'},
    )

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，外键关联账套年度')
    fiscal_year = db.Column(db.Integer, primary_key=True, comment='会计年度，4位如2021')
    internal_org_code = db.Column(db.String(50), primary_key=True, comment='内设机构编码，对应 XML 内设机构编码')
    internal_org_name = db.Column(db.String(200), nullable=False, comment='内设机构名称，对应 XML 内设机构名称')
    parent_org_code = db.Column(db.String(50), comment='上级机构编码，对应 XML 上级机构编码')
    remark = db.Column(db.String(500), comment='备注')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1=启用 0=停用')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        """返回字典"""
        return {
            'account_book_code': self.account_book_code,
            'fiscal_year': self.fiscal_year,
            'internal_org_code': self.internal_org_code,
            'internal_org_name': self.internal_org_name,
            'parent_org_code': self.parent_org_code,
            'remark': self.remark,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
