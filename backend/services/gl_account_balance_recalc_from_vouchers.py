# -*- coding: utf-8 -*-
"""
从记账凭证分录重算科目余额（总账默认 currency 为空），写入 gl_account_balance，并填写 ParentCode（父级科目）。

凭证分录均为明细科目。gl_voucher_entry.period_number=0 表示期初/年初凭证，参与滚算并写入 period_number=0
的余额行；其后 1 月起期初为上期末（含 0 期结转结果）。

可选传入级次规则（如 "422" 表示各级累计编码长度 4、6、8），
则按明细滚算后，将各级上级科目的发生额与余额按「明细前缀归属」汇总写入。

重算前会删除该账套、该年度下 gl_account_balance 中的全部行。

事务由调用方 commit/rollback；本函数不提交事务。
"""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func

from Model import (
    db,
    Account,
    GLAccountBalance,
    GLVoucherEntry,
)

_q2 = Decimal("0.01")


def _d(v: Any) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _quantize(d: Decimal) -> Decimal:
    return d.quantize(_q2, rounding=ROUND_HALF_UP)


def _closing_balance_and_dir(
    signed: Decimal, nature: str
) -> tuple[Decimal, str]:
    """将「按科目自然方向」的带符号净额转为非负金额 + 借/贷。"""
    s = _quantize(signed)
    if nature == "借":
        if s >= 0:
            return abs(s), "借"
        return abs(s), "贷"
    if s >= 0:
        return abs(s), "贷"
    return abs(s), "借"


def _universal_to_display(signed_u: Decimal, nature: str) -> tuple[Decimal, str]:
    """
    将「借正贷负」统一轴上的余额转为该科目性质下的 (金额, 方向)。
    滚算在统一轴：signed_u + 本期借 - 本期贷。
    """
    su = _quantize(signed_u)
    if nature == "借":
        return _closing_balance_and_dir(su, "借")
    return _closing_balance_and_dir(-su, "贷")


def _next_signed_universal(
    signed_u: Decimal, debit: Decimal, credit: Decimal
) -> Decimal:
    return _quantize(_quantize(signed_u) + _quantize(debit) - _quantize(credit))


def parse_level_pattern(pattern: str | None) -> list[int] | None:
    """
    解析前端级次规则，如 "422" → 累计长度 [4, 6, 8]（每段长度为一位数字 1–9）。
    若 pattern 为空或仅空白，返回 None（不按级次汇总，仅保留凭证明细科目行）。
    非法则抛 ValueError。
    """
    if pattern is None:
        return None
    s = str(pattern).strip()
    if not s:
        return None
    if not re.fullmatch(r"[1-9]+", s):
        raise ValueError(
            "level_pattern 须为非空数字串，每位表示一级科目编码长度增量（仅允许 1–9），例如 422"
        )
    cum = 0
    out: list[int] = []
    for ch in s:
        cum += int(ch)
        out.append(cum)
    return out


def _nodes_for_leaf(leaf: str, cum: list[int]) -> set[str]:
    """由明细编码与累计级长生成该明细对应的各级科目编码（含自身）。"""
    nodes: set[str] = set()
    for L in cum:
        if len(leaf) >= L:
            nodes.add(leaf[:L])
    nodes.add(leaf)
    return nodes


def _derive_parent_from_pattern(node: str, cum: list[int]) -> str | None:
    """
    按累计编码长度推断直接上级科目：node 长度若等于 cum 中某档，则上级为上一档长度之前缀；
    否则取小于 len(node) 的最大档长作为上级前缀长度。
    """
    if not node or not cum:
        return None
    nlen = len(node)
    if nlen in cum:
        idx = cum.index(nlen)
        if idx == 0:
            return None
        return node[: cum[idx - 1]]
    smaller = [L for L in cum if L < nlen]
    if not smaller:
        return None
    return node[: max(smaller)]


def _parent_code_for_node(
    node: str,
    acc_recs: dict[str, Account],
    cum_levels: list[int] | None,
    rollup: bool,
) -> str | None:
    """
    父级科目编号：优先会计科目表 parent_account_code；否则在启用级次规则时按编码规则推断。
    """
    rec = acc_recs.get(node)
    if rec and (rec.parent_account_code or "").strip():
        return (rec.parent_account_code or "").strip()
    if rollup and cum_levels:
        derived = _derive_parent_from_pattern(node, cum_levels)
        if derived:
            return derived
    return None


def recalculate_gl_account_balance_from_vouchers(
    account_book_code: str,
    fiscal_year: int,
    level_pattern: str | None = None,
) -> dict[str, Any]:
    """
    按账套、年度以凭证为唯一来源重算 gl_account_balance（currency_code 为 NULL，parent_code 已填）。

    level_pattern:
      - None / ""：每个凭证明细科目单独一行，不生成上级汇总行。
      - 如 "422"：一级 4 位、二级累计 6 位、三级累计 8 位；对每条明细滚算后，
        再按编码前缀将发生额与余额汇总到各级上级科目。

    不调用 db.session.commit()。
    """
    account_book_code = (account_book_code or "").strip()
    if not account_book_code:
        raise ValueError("account_book_code 不能为空")

    cum_levels = parse_level_pattern(level_pattern)
    rollup = cum_levels is not None

    deleted = (
        GLAccountBalance.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
        ).delete(synchronize_session=False)
    )

    acc_rows = (
        db.session.query(GLVoucherEntry.account_code)
        .filter(
            GLVoucherEntry.account_book_code == account_book_code,
            GLVoucherEntry.fiscal_year == fiscal_year,
        )
        .distinct()
        .all()
    )
    leaf_set_list = sorted({r[0] for r in acc_rows if r[0]})
    leaf_set = set(leaf_set_list)

    if not leaf_set:
        db.session.flush()
        return {
            "deleted_rows": deleted,
            "account_count": 0,
            "inserted_rows": 0,
            "periods_emitted": 0,
            "unknown_accounts": [],
            "level_pattern_applied": None,
            "includes_period_0": False,
        }

    # 汇总 (account_code, period_number) -> (debit, credit)，仅明细
    sums = (
        db.session.query(
            GLVoucherEntry.account_code,
            GLVoucherEntry.period_number,
            func.coalesce(func.sum(GLVoucherEntry.debit_amount), 0),
            func.coalesce(func.sum(GLVoucherEntry.credit_amount), 0),
        )
        .filter(
            GLVoucherEntry.account_book_code == account_book_code,
            GLVoucherEntry.fiscal_year == fiscal_year,
        )
        .group_by(GLVoucherEntry.account_code, GLVoucherEntry.period_number)
        .all()
    )

    # period_number=0：期初/年初调整凭证；1–12（或 13）为各月。须先滚算 0 期，再滚 1 月起。
    mov: dict[tuple[str, int], tuple[Decimal, Decimal]] = {}
    max_p = 12
    has_period_0 = False
    for acc, per, dsum, csum in sums:
        if per is None or acc is None:
            continue
        p = int(per)
        if p < 0 or p > 13:
            continue
        mov[(acc, p)] = (_d(dsum), _d(csum))
        if p == 0:
            has_period_0 = True
        elif p >= 1:
            max_p = max(max_p, p)
    max_p = min(max(max_p, 12), 13)
    period_list: list[int] = []
    if has_period_0:
        period_list.append(0)
    period_list.extend(range(1, max_p + 1))

    # 需出账的科目集合
    if rollup:
        all_nodes: set[str] = set()
        for leaf in leaf_set:
            all_nodes |= _nodes_for_leaf(leaf, cum_levels)
    else:
        all_nodes = set(leaf_set)

    all_nodes_sorted = sorted(all_nodes, key=lambda x: (len(x), x))

    # 科目性质：所有可能出现的科目编码
    acc_recs_list = Account.query.filter(
        Account.account_book_code == account_book_code,
        Account.fiscal_year == fiscal_year,
        Account.account_code.in_(list(all_nodes)),
    ).all()
    acc_recs: dict[str, Account] = {a.account_code: a for a in acc_recs_list}

    nature_by_code: dict[str, str] = {}
    unknown_accounts: list[str] = []
    for code in all_nodes_sorted:
        rec = acc_recs.get(code)
        if rec and (rec.balance_direction or "").strip() in ("借", "贷"):
            nature_by_code[code] = rec.balance_direction.strip()
        else:
            nature_by_code[code] = "借"
            if code in leaf_set:
                unknown_accounts.append(code)

    # 每个明细在各期的「借正贷负」轴上的期初/期末（0 期从 0 滚到期初后余额；1 月期初=0 期期末）
    leaf_signed_start: dict[tuple[str, int], Decimal] = {}
    leaf_signed_end: dict[tuple[str, int], Decimal] = {}

    for leaf in leaf_set_list:
        signed_u = Decimal("0")
        for p in period_list:
            leaf_signed_start[(leaf, p)] = signed_u
            d_amt, c_amt = mov.get((leaf, p), (Decimal("0"), Decimal("0")))
            signed_u = _next_signed_universal(signed_u, d_amt, c_amt)
            leaf_signed_end[(leaf, p)] = signed_u

    # 每个科目节点对应的明细集合（用于汇总）
    descendants_map: dict[str, list[str]] = {}
    for node in all_nodes_sorted:
        if rollup:
            descendants_map[node] = sorted(
                [
                    lf
                    for lf in leaf_set
                    if lf.startswith(node) and len(lf) >= len(node)
                ]
            )
        else:
            descendants_map[node] = [node] if node in leaf_set else []

    to_add: list[GLAccountBalance] = []
    for node in all_nodes_sorted:
        leaves = descendants_map.get(node) or []
        nature = nature_by_code[node]
        for p in period_list:
            su_open = _quantize(
                sum(leaf_signed_start.get((lf, p), Decimal("0")) for lf in leaves)
            )
            su_end = _quantize(
                sum(leaf_signed_end.get((lf, p), Decimal("0")) for lf in leaves)
            )
            d_amt = _quantize(
                sum(mov.get((lf, p), (Decimal("0"), Decimal("0")))[0] for lf in leaves)
            )
            c_amt = _quantize(
                sum(mov.get((lf, p), (Decimal("0"), Decimal("0")))[1] for lf in leaves)
            )
            o_bal, o_dir = _universal_to_display(su_open, nature)
            c_bal, c_dir = _universal_to_display(su_end, nature)
            parent_code = _parent_code_for_node(node, acc_recs, cum_levels, rollup)

            to_add.append(
                GLAccountBalance(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    period_number=p,
                    account_code=node,
                    opening_balance=o_bal,
                    opening_balance_direction=o_dir,
                    current_period_debit_amount=d_amt,
                    current_period_credit_amount=c_amt,
                    closing_balance=c_bal,
                    closing_balance_direction=c_dir,
                    currency_code=None,
                    parent_code=parent_code,
                )
            )

    for obj in to_add:
        db.session.add(obj)
    db.session.flush()

    return {
        "deleted_rows": deleted,
        "account_count": len(all_nodes_sorted),
        "inserted_rows": len(to_add),
        "periods_emitted": len(period_list) if all_nodes_sorted else 0,
        "includes_period_0": has_period_0,
        "unknown_accounts": sorted(set(unknown_accounts)),
        "level_pattern_applied": level_pattern.strip() if (rollup and level_pattern) else None,
    }
