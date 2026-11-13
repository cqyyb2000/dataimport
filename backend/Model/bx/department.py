# 报销台账部门（按年度，多级）
from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from ..base import db


class BxDepartment(db.Model):
    """报销台账部门。同一年度部门代码唯一，上级必须是同一年度的部门。"""

    __tablename__ = 'bx_department'
    __table_args__ = (
        ForeignKeyConstraint(
            ['fiscal_year', 'parent_dept_code'],
            ['bx_department.fiscal_year', 'bx_department.dept_code'],
            ondelete='RESTRICT',
            onupdate='CASCADE',
            name='fk_bx_department_parent',
        ),
        CheckConstraint('level_no >= 1', name='chk_bx_department_level'),
        {'comment': '报销台账部门，按年度多级存放，与账套内设机构无关'},
    )

    fiscal_year = db.Column(db.Integer, primary_key=True, comment='年度，4位')
    dept_code = db.Column(db.String(50), primary_key=True, comment='部门代码，同一年度内唯一')
    dept_name = db.Column(db.String(200), nullable=False, comment='部门名称')
    parent_dept_code = db.Column(db.String(50), comment='上级部门代码，空表示第一级')
    level_no = db.Column(db.SmallInteger, nullable=False, comment='级次，第一级为 1，下级比直接上级大 1')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        return {
            'fiscal_year': self.fiscal_year,
            'dept_code': self.dept_code,
            'dept_name': self.dept_name,
            'parent_dept_code': self.parent_dept_code,
            'level_no': self.level_no,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
