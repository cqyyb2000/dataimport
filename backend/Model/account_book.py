# 账套信息表模型（主表，与 XML 电子账簿一一对应，不含会计年度；会计年度在从表，主从关系）
from .base import db


class AccountBook(db.Model):
    """账套信息表（主表），对应 XML 电子账簿结构，不含会计年度；会计年度单独在从表 account_book_fiscal_year"""
    __tablename__ = 'account_book'
    __table_args__ = {'comment': '账套信息表（主表），对应 XML 电子账簿，不含会计年度'}

    account_book_code = db.Column(db.String(50), primary_key=True, comment='账套编码，对应电子账簿编号')
    account_book_name = db.Column(db.String(200), nullable=False, comment='账套名称')
    accounting_entity = db.Column(db.String(200), nullable=False, comment='会计核算单位')
    organization_code = db.Column(db.String(20), comment='组织机构代码')
    unit_type = db.Column(db.String(50), nullable=False, comment='单位类型：行政单位/事业单位')
    industry = db.Column(db.String(50), comment='所属行业')
    administrative_division_code = db.Column(db.String(20), comment='行政区划代码')
    budget_management_level = db.Column(db.String(50), comment='预算管理级次')
    funding_source = db.Column(db.String(50), comment='经费来源')
    developer = db.Column(db.String(200), comment='开发单位')
    version = db.Column(db.String(50), comment='软件版本号')
    base_currency = db.Column(db.String(50), nullable=False, comment='本位币名称')
    standard_version = db.Column(db.String(20), nullable=False, comment='标准版本号')
    default_fiscal_year = db.Column(db.Integer, comment='默认会计年度')
    remark = db.Column(db.String(500), comment='备注')
    status = db.Column(db.SmallInteger, default=1, comment='状态：1=启用 0=停用')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 主从关系：会计年度单独在从表，一账套多年度
    fiscal_years = db.relationship('AccountBookFiscalYear', backref='account_book', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """返回字典，imported_fiscal_years 从关联表汇总为排序后的年度列表"""
        imported = [f.fiscal_year for f in self.fiscal_years]
        imported.sort()
        return {
            'account_book_code': self.account_book_code,
            'account_book_name': self.account_book_name,
            'accounting_entity': self.accounting_entity,
            'organization_code': self.organization_code,
            'unit_type': self.unit_type,
            'industry': self.industry,
            'administrative_division_code': self.administrative_division_code,
            'budget_management_level': self.budget_management_level,
            'funding_source': self.funding_source,
            'developer': self.developer,
            'version': self.version,
            'base_currency': self.base_currency,
            'standard_version': self.standard_version,
            'default_fiscal_year': self.default_fiscal_year,
            'imported_fiscal_years': imported,
            'remark': self.remark,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
