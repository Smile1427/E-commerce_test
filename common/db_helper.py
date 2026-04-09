"""
数据库测试辅助模块
用于在测试中直接查询和验证数据库状态
"""
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from pathlib import Path

# 数据库路径（相对于项目根目录）
DB_PATH = Path(__file__).parent.parent / "ecommerce.db"


@contextmanager
def get_test_db():
    """获取测试数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class DatabaseVerifier:
    """数据库验证器 - 用于测试断言"""

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Dict]:
        """根据ID获取商品"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_cart_items(user_id: int) -> List[Dict]:
        """获取用户购物车"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_orders_by_user(user_id: int) -> List[Dict]:
        """获取用户订单"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY create_time DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Dict]:
        """根据ID获取订单"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_order_items(order_id: int) -> List[Dict]:
        """获取订单商品明细"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_product_stock(product_id: int) -> int:
        """获取商品库存"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return row['stock'] if row else 0

    @staticmethod
    def get_product_sales(product_id: int) -> int:
        """获取商品销量"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sales FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return row['sales'] if row else 0

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """检查Token是否在黑名单中"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM token_blacklist WHERE token = ?", (token,))
            return cursor.fetchone() is not None

    @staticmethod
    def get_cart_count(user_id: int) -> int:
        """获取购物车商品种类数"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM carts WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    @staticmethod
    def get_cart_total_quantity(user_id: int) -> int:
        """获取购物车商品总数量"""
        with get_test_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(quantity) FROM carts WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row[0] else 0


# 创建全局实例
db = DatabaseVerifier()