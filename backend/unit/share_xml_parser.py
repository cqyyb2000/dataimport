# -*- coding: utf-8 -*-
"""
公共档案类 SHARE.xml 解析工具

依据 GB/T 24589.2-2010 数据接口规范，解析 公共档案类/SHARE.xml，
按类别输出 JSON 格式的返回内容。

支持的类别（按标准及实际文件）：
- 电子账簿、会计期间、内设机构、会计科目、科目辅助核算
- 币种、汇率、汇率类型
- 项目、部门、人员、单位往来、个人往来
- 自定义项、自定义档案项、自定义档案值
"""

import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


# 公共档案根元素可能使用的命名空间（解析时忽略）
NS = "http://sxbw.audit.gov.cn/AccountingSoftwareDataInterfaceStandard/2010/PSGA/XMLSchema"


def _local_tag(tag: str) -> str:
    """去掉命名空间，返回本地标签名。"""
    if tag.startswith("{") and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _element_to_dict(element: ET.Element) -> dict[str, Any]:
    """
    将 XML 元素转为字典。
    仅处理直接子元素：标签名 -> 文本内容（空标签为 ''）。
    不递归处理嵌套结构，符合公共档案“一层子节点”的结构。
    """
    result = {}
    for child in element:
        local = _local_tag(child.tag)
        text = (child.text or "").strip() if child.text is not None else ""
        # 空元素或自闭合如 <上级机构编码/>
        if not text and len(child) == 0:
            text = ""
        result[local] = text
    return result


def _parse_tree_to_share_dict(
    root: ET.Element,
    as_dict: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """从已解析的 XML 根节点按类别聚合为字典（供 parse_share_xml / 流式解析复用）。"""
    by_category: dict[str, list[dict[str, Any]]] = {}
    for child in root:
        local = _local_tag(child.tag)
        item = _element_to_dict(child)
        if not item:
            continue
        if local not in by_category:
            by_category[local] = []
        by_category[local].append(item)
    return by_category


def parse_share_xml(
    file_path: str | Path | Any,
    *,
    encoding: str = "utf-8",
    as_dict: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """
    解析公共档案类 SHARE.xml，按类别输出 JSON 结构。
    支持传入文件路径（str/Path）或文件流（含 read 方法的对象，如上传的 FileStorage）。

    :param file_path: SHARE.xml 文件路径（字符串或 Path）或文件流对象
    :param encoding: 文件编码，默认 utf-8
    :param as_dict: 为 True 时返回字典（默认）；为 False 时返回可 JSON 序列化的同等结构
    :return: 按类别分组的字典，每个类别的值为该类别下全部条目的明细列表（每条为字段名->取值的字典），形如：
             {
               "电子账簿": [ {"电子账簿编号": "XZ001", "电子账簿名称": "行政账", ...} ],
               "会计期间": [ {"会计年度": "2021", "会计期间号": "1", ...}, ... ],
               "内设机构": [ {"内设机构编码": "0001", "内设机构名称": "会领导", ...}, ... ],
               "项目": [ {"项目编码": "0001", "项目名称": "基本支出", ...}, ... ],
               "自定义档案项": [ {...}, ... ],
               "自定义档案值": [ {...}, ... ],
               "币种": [ {...}, ... ],
               "汇率类型": [ {...}, ... ],
               ...
             }
             若某类别在文件中不存在，则不会出现在返回结果中。
    """
    if hasattr(file_path, "read"):
        tree = ET.parse(file_path, parser=ET.XMLParser(encoding=encoding))
    else:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        tree = ET.parse(path, parser=ET.XMLParser(encoding=encoding))
    root = tree.getroot()
    root_local = _local_tag(root.tag)
    if root_local != "公共档案":
        raise ValueError(f"根元素应为「公共档案」，当前为: {root_local}")
    by_category = _parse_tree_to_share_dict(root, as_dict=as_dict)
    return by_category


def parse_share_xml_to_json_string(
    file_path: str | Path,
    *,
    encoding: str = "utf-8",
    ensure_ascii: bool = False,
    indent: int | None = 2,
) -> str:
    """
    解析 SHARE.xml 并直接返回 JSON 字符串。

    :param file_path: SHARE.xml 文件路径
    :param encoding: 文件编码
    :param ensure_ascii: 是否转义非 ASCII（默认 False，保留中文）
    :param indent: 缩进空格数，None 表示不缩进
    :return: JSON 字符串
    """
    data = parse_share_xml(file_path, encoding=encoding, as_dict=True)
    return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)


def get_category_json(
    share_data: dict[str, list[dict[str, Any]]],
    category_name: str,
) -> list[dict[str, Any]]:
    """
    从 parse_share_xml 返回的完整 JSON 中，取出指定类别的明细数据。

    :param share_data: parse_share_xml 返回的按类别分组的字典
    :param category_name: 类别名称，如 "电子账簿"、"会计期间"、"内设机构"、"项目"、"自定义档案值" 等
    :return: 该类别下全部条目的列表（每条为字段名->取值的字典）；若类别不存在则返回空列表 []
    """
    return share_data.get(category_name, [])


if __name__ == "__main__":
    import sys
    # 支持命令行传入路径: python -m unit.share_xml_parser [SHARE.xml路径]
    if len(sys.argv) >= 2:
        xml_path = Path(sys.argv[1])
    else:
        xml_path = Path(__file__).resolve().parent.parent / "公共档案类" / "SHARE.xml"
    if not xml_path.exists():
        print(f"未找到文件: {xml_path}", file=sys.stderr)
        sys.exit(1)
    result = parse_share_xml(xml_path)
    # 输出完整 JSON：每个类别下均为该类别全部条目的明细数据
    print(json.dumps(result, ensure_ascii=False, indent=2))
