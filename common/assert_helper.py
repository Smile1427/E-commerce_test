# common/assert_helper.py
"""
断言辅助工具
"""
import json
from typing import Any, Dict, List, Optional


class AssertHelper:
    """断言助手"""

    @staticmethod
    def assert_status_code(response, expected: int, message: str = ""):
        """断言HTTP状态码"""
        assert response.status_code == expected, \
            f"{message} 期望状态码: {expected}, 实际: {response.status_code}"

    @staticmethod
    def assert_business_code(response, expected: int = 200, message: str = ""):
        """断言业务状态码"""
        body = response.json()
        actual = body.get('code')
        assert actual == expected, \
            f"{message} 期望业务码: {expected}, 实际: {actual}, 消息: {body.get('message')}"

    @staticmethod
    def assert_field_exists(data: Dict, field: str, message: str = ""):
        """断言字段存在"""
        assert field in data, f"{message} 字段 '{field}' 不存在，实际字段: {list(data.keys())}"

    @staticmethod
    def assert_field_value(data: Dict, field: str, expected: Any, message: str = ""):
        """断言字段值"""
        AssertHelper.assert_field_exists(data, field, message)
        actual = data[field]
        assert actual == expected, \
            f"{message} 字段 '{field}' 期望: {expected}, 实际: {actual}"

    @staticmethod
    def assert_list_not_empty(data: List, message: str = ""):
        """断言列表非空"""
        assert len(data) > 0, f"{message} 列表为空"

    @staticmethod
    def assert_greater_than(actual: Any, expected: Any, message: str = ""):
        """断言大于"""
        assert actual > expected, f"{message} 期望 {actual} > {expected}"

    @staticmethod
    def assert_between(value: Any, min_val: Any, max_val: Any, message: str = ""):
        """断言在范围内"""
        assert min_val <= value <= max_val, \
            f"{message} 期望 {value} 在 [{min_val}, {max_val}] 之间"