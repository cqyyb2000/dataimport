# 报销单单据号年月流水（只增不减）
from sqlalchemy import CheckConstraint

from ..base import db


class BxDocSeq(db.Model):
    """每个年月已发出的最大流水号。删除单据或改月放弃原号时不减小。"""

    __tablename__ = 'bx_doc_seq'
    __table_args__ = (
        CheckConstraint('fiscal_month BETWEEN 1 AND 12', name='chk_bx_doc_seq_month'),
        CheckConstraint('max_seq BETWEEN 0 AND 9999', name='chk_bx_doc_seq_max'),
        {'comment': '报销单据号流水，按报销时间的年月分别编号'},
    )

    fiscal_year = db.Column(db.Integer, primary_key=True, comment='年度，4位')
    fiscal_month = db.Column(db.SmallInteger, primary_key=True, comment='月份，1到12')
    max_seq = db.Column(db.Integer, nullable=False, default=0, comment='该年月已发出的最大流水号，0到9999')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    def to_dict(self):
        return {
            'fiscal_year': self.fiscal_year,
            'fiscal_month': self.fiscal_month,
            'max_seq': self.max_seq,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
