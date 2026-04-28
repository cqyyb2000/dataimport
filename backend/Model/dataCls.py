# 兼容旧导入：从独立模型文件统一导出
from . import (
    db,
    User,
    Menu,
    Permission,
    AccountBookFiscalYear,
    AccountBook,
    InternalOrganization,
)

__all__ = [
    'db',
    'User',
    'Menu',
    'Permission',
    'AccountBookFiscalYear',
    'AccountBook',
    'InternalOrganization',
]
