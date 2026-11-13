# -*- coding: utf-8 -*-
"""报销台账业务错误。路由层据此决定是普通失败，还是弹出确认。"""


class BxError(Exception):
    """规则不允许继续，数据保持原样。"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BxOverspend(BxError):
    """本次金额计入后余额会变成负数。调用方未确认时不写库。"""

    def __init__(self, message: str, budget_amount, confirmed_amount, this_amount):
        super().__init__(message)
        self.budget_amount = budget_amount
        self.confirmed_amount = confirmed_amount
        self.this_amount = this_amount


class BxNeedConfirm(BxError):
    """目标年度已有档案或预算。调用方确认后才会清空并复制。"""

    def __init__(self, message: str, source_year: int, target_year: int,
                 department_count: int, project_count: int, budget_count: int):
        super().__init__(message)
        self.source_year = source_year
        self.target_year = target_year
        self.department_count = department_count
        self.project_count = project_count
        self.budget_count = budget_count
