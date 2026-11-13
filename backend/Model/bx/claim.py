# 报销台账单据
from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from ..base import db


class BxClaim(db.Model):
    """报销单。单据号全局唯一；部门、项目、年度必须对应一条预算。"""

    STATUS_PENDING = '待支出'
    STATUS_CONFIRMED = '已计入'

    __tablename__ = 'bx_claim'
    __table_args__ = (
        ForeignKeyConstraint(
            ['fiscal_year', 'dept_code', 'project_code'],
            ['bx_budget.fiscal_year', 'bx_budget.dept_code', 'bx_budget.project_code'],
            ondelete='RESTRICT',
            onupdate='CASCADE',
            name='fk_bx_claim_budget',
        ),
        CheckConstraint('amount > 0', name='chk_bx_claim_amount'),
        CheckConstraint("status IN ('待支出', '已计入')", name='chk_bx_claim_status'),
        {'comment': '报销台账报销单'},
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
        comment='内部主键',
    )
    doc_no = db.Column(db.String(10), nullable=False, unique=True, comment='单据号，年度4位+月份2位+流水4位')
    fiscal_year = db.Column(db.Integer, nullable=False, comment='所属年度，与报销时间的年份一致')
    expense_date = db.Column(db.Date, nullable=False, comment='报销时间，精确到日期')
    dept_code = db.Column(db.String(50), nullable=False, comment='部门代码')
    project_code = db.Column(db.String(50), nullable=False, comment='项目代码')
    claimant = db.Column(db.String(100), nullable=False, comment='报销人')
    summary = db.Column(db.String(500), nullable=False, comment='摘要')
    amount = db.Column(db.Numeric(18, 2), nullable=False, comment='报销金额，大于 0')
    status = db.Column(db.String(10), nullable=False, comment='状态：待支出、已计入')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        return {
            'id': self.id,
            'doc_no': self.doc_no,
            'fiscal_year': self.fiscal_year,
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'dept_code': self.dept_code,
            'project_code': self.project_code,
            'claimant': self.claimant,
            'summary': self.summary,
            'amount': f'{self.amount:.2f}' if self.amount is not None else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
