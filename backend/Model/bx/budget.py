# 报销台账预算（年度 + 部门 + 项目 唯一）
from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from ..base import db


class BxBudget(db.Model):
    """报销台账预算。同一年度、同一部门、同一项目只有一条。部门和项目都应是最明细级，由服务层校验。"""

    __tablename__ = 'bx_budget'
    __table_args__ = (
        ForeignKeyConstraint(
            ['fiscal_year', 'dept_code'],
            ['bx_department.fiscal_year', 'bx_department.dept_code'],
            ondelete='RESTRICT',
            onupdate='CASCADE',
            name='fk_bx_budget_department',
        ),
        ForeignKeyConstraint(
            ['fiscal_year', 'project_code'],
            ['bx_project.fiscal_year', 'bx_project.project_code'],
            ondelete='RESTRICT',
            onupdate='CASCADE',
            name='fk_bx_budget_project',
        ),
        CheckConstraint('amount >= 0', name='chk_bx_budget_amount'),
        {'comment': '报销台账预算，年度+部门+项目唯一'},
    )

    fiscal_year = db.Column(db.Integer, primary_key=True, comment='年度，4位')
    dept_code = db.Column(db.String(50), primary_key=True, comment='部门代码')
    project_code = db.Column(db.String(50), primary_key=True, comment='项目代码')
    amount = db.Column(db.Numeric(18, 2), nullable=False, comment='预算金额，大于等于 0')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        return {
            'fiscal_year': self.fiscal_year,
            'dept_code': self.dept_code,
            'project_code': self.project_code,
            'amount': f'{self.amount:.2f}' if self.amount is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
