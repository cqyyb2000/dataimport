# 报销台账项目（按年度，多级）
from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from ..base import db


class BxProject(db.Model):
    """报销台账项目。同一年度项目代码唯一，上级必须是同一年度的项目。"""

    __tablename__ = 'bx_project'
    __table_args__ = (
        ForeignKeyConstraint(
            ['fiscal_year', 'parent_project_code'],
            ['bx_project.fiscal_year', 'bx_project.project_code'],
            ondelete='RESTRICT',
            onupdate='CASCADE',
            name='fk_bx_project_parent',
        ),
        CheckConstraint('level_no >= 1', name='chk_bx_project_level'),
        {'comment': '报销台账项目，按年度多级存放，与账套项目档案无关'},
    )

    fiscal_year = db.Column(db.Integer, primary_key=True, comment='年度，4位')
    project_code = db.Column(db.String(50), primary_key=True, comment='项目代码，同一年度内唯一')
    project_name = db.Column(db.String(200), nullable=False, comment='项目名称')
    parent_project_code = db.Column(db.String(50), comment='上级项目代码，空表示第一级')
    level_no = db.Column(db.SmallInteger, nullable=False, comment='级次，第一级为 1，下级比直接上级大 1')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        return {
            'fiscal_year': self.fiscal_year,
            'project_code': self.project_code,
            'project_name': self.project_name,
            'parent_project_code': self.parent_project_code,
            'level_no': self.level_no,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
