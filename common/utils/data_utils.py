"""
数据处理工具

提供字典、列表等数据结构的处理函数。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Union


def deep_merge(
    base: Dict[str, Any],
    override: Dict[str, Any],
    inplace: bool = False,
) -> Dict[str, Any]:
    """
    深度合并两个字典

    Args:
        base: 基础字典
        override: 覆盖字典
        inplace: 是否原地修改

    Returns:
        合并后的字典
    """
    if not inplace:
        base = copy.deepcopy(base)

    for key, value in override.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            base[key] = deep_merge(base[key], value, inplace=True)
        else:
            base[key] = copy.deepcopy(value)

    return base


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """
    扁平化字典

    Args:
        d: 输入字典
        parent_key: 父键前缀
        sep: 分隔符

    Returns:
        扁平化后的字典
    """
    items: list = []

    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))

    return dict(items)


def unflatten_dict(
    d: Dict[str, Any],
    sep: str = ".",
) -> Dict[str, Any]:
    """
    反扁平化字典

    Args:
        d: 扁平化的字典
        sep: 分隔符

    Returns:
        嵌套字典
    """
    result: Dict[str, Any] = {}

    for key, value in d.items():
        parts = key.split(sep)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def safe_get(
    d: Dict[str, Any],
    key: str,
    default: Any = None,
    sep: str = ".",
) -> Any:
    """
    安全获取嵌套字典的值

    Args:
        d: 输入字典
        key: 键路径（支持点分隔）
        default: 默认值
        sep: 分隔符

    Returns:
        获取的值或默认值
    """
    if not d:
        return default

    keys = key.split(sep)
    current = d

    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default

    return current


def safe_set(
    d: Dict[str, Any],
    key: str,
    value: Any,
    sep: str = ".",
) -> Dict[str, Any]:
    """
    安全设置嵌套字典的值

    Args:
        d: 输入字典
        key: 键路径（支持点分隔）
        value: 要设置的值
        sep: 分隔符

    Returns:
        修改后的字典
    """
    keys = key.split(sep)
    current = d

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value
    return d


def deep_copy(obj: Any) -> Any:
    """
    深度复制对象

    Args:
        obj: 要复制的对象

    Returns:
        复制后的对象
    """
    return copy.deepcopy(obj)


def dict_diff(
    d1: Dict[str, Any],
    d2: Dict[str, Any],
) -> Dict[str, Any]:
    """
    比较两个字典的差异

    Args:
        d1: 第一个字典
        d2: 第二个字典

    Returns:
        差异字典
    """
    diff: Dict[str, Any] = {
        "added": {},
        "removed": {},
        "changed": {},
        "unchanged": {},
    }

    all_keys = set(d1.keys()) | set(d2.keys())

    for key in all_keys:
        if key not in d1:
            diff["added"][key] = d2[key]
        elif key not in d2:
            diff["removed"][key] = d1[key]
        elif d1[key] != d2[key]:
            diff["changed"][key] = {"old": d1[key], "new": d2[key]}
        else:
            diff["unchanged"][key] = d1[key]

    return diff


def list_to_dict(
    lst: List[Any],
    key: str,
) -> Dict[str, Any]:
    """
    将列表转换为字典

    Args:
        lst: 输入列表
        key: 作为键的字段名

    Returns:
        转换后的字典
    """
    result = {}
    for item in lst:
        if isinstance(item, dict) and key in item:
            result[item[key]] = item
    return result


def dict_to_list(
    d: Dict[str, Any],
    key_name: str = "key",
) -> List[Dict[str, Any]]:
    """
    将字典转换为列表

    Args:
        d: 输入字典
        key_name: 键的字段名

    Returns:
        转换后的列表
    """
    result = []
    for key, value in d.items():
        if isinstance(value, dict):
            item = {key_name: key, **value}
        else:
            item = {key_name: key, "value": value}
        result.append(item)
    return result


def remove_none_values(
    d: Dict[str, Any],
    recursive: bool = True,
) -> Dict[str, Any]:
    """
    移除字典中的 None 值

    Args:
        d: 输入字典
        recursive: 是否递归处理嵌套字典

    Returns:
        处理后的字典
    """
    result = {}

    for key, value in d.items():
        if value is not None:
            if recursive and isinstance(value, dict):
                value = remove_none_values(value, recursive=True)
            result[key] = value

    return result


def get_nested_keys(
    d: Dict[str, Any],
    sep: str = ".",
    prefix: str = "",
) -> List[str]:
    """
    获取嵌套字典的所有键路径

    Args:
        d: 输入字典
        sep: 分隔符
        prefix: 键前缀

    Returns:
        键路径列表
    """
    keys: List[str] = []

    for key, value in d.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key

        if isinstance(value, dict):
            keys.extend(get_nested_keys(value, sep, full_key))
        else:
            keys.append(full_key)

    return keys
