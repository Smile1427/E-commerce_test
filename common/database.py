"""
数据库管理模块
使用 SQLite 存储用户、商品、购物车、订单数据
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = "ecommerce.db"


@contextmanager
def get_db():
    """获取数据库连接（上下文管理器）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使返回结果支持字典访问
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"数据库错误: {e}")
        raise
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                avatar TEXT,
                status INTEGER DEFAULT 1,
                role TEXT DEFAULT 'user',
                create_time TEXT NOT NULL
            )
        ''')

        # 2. 商品分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')

        # 3. 商品表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER,
                price REAL NOT NULL,
                original_price REAL,
                stock INTEGER DEFAULT 0,
                sales INTEGER DEFAULT 0,
                status INTEGER DEFAULT 1,
                main_image TEXT,
                description TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')

        # 4. 购物车表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cart_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                selected INTEGER DEFAULT 1,
                create_time TEXT NOT NULL,
                update_time TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # 5. 订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status INTEGER DEFAULT 0,
                address TEXT NOT NULL,
                remark TEXT,
                create_time TEXT NOT NULL,
                pay_time TEXT,
                ship_time TEXT,
                confirm_time TEXT,
                expire_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # 6. 订单商品明细表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                product_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # 7. Token 黑名单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                create_time TEXT NOT NULL
            )
        ''')

        logger.info("数据库表结构初始化完成")


def init_test_data():
    """初始化测试数据"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            logger.info("测试数据已存在，跳过初始化")
            return

        # 插入用户数据
        users = [
            (1, "testuser", "test@example.com", "Test123456", "13800138000", None, 1, "user", "2024-01-01 10:00:00"),
            (2, "vipuser", "vip@example.com", "Vip123456", "13900139000", None, 1, "vip", "2024-01-15 14:30:00"),
        ]
        cursor.executemany('''
            INSERT INTO users (id, username, email, password, phone, avatar, status, role, create_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', users)

        # 插入分类数据
        categories = [
            (1, "手机数码", 0, 1),
            (2, "电脑办公", 0, 1),
            (3, "家用电器", 0, 1),
            (11, "智能手机", 1, 2),
            (12, "智能穿戴", 1, 2),
        ]
        cursor.executemany('''
            INSERT INTO categories (id, name, parent_id, level)
            VALUES (?, ?, ?, ?)
        ''', categories)

        # 插入商品数据
        products = [
            (1, "小米14 Ultra", 11, 6499, 6999, 100, 520, 1, "url1", "徕卡光学，影像旗舰"),
            (2, "华为 Mate 60 Pro", 11, 6999, 6999, 50, 380, 1, "url2", "麒麟芯片，卫星通话"),
            (3, "iPhone 15 Pro", 11, 7999, 8999, 80, 620, 1, "url3", "A17 Pro芯片"),
            (4, "Apple Watch S9", 12, 2999, 3199, 200, 310, 1, "url4", "全天候视网膜屏"),
            (5, "联想拯救者Y9000P", 2, 8999, 9999, 30, 150, 1, "url5", "游戏本，RTX4060"),
            (6, "小米手环8 Pro", 12, 399, 449, 500, 1200, 1, "url6", "大屏健康监测"),
            (7, "罗技G502鼠标", 2, 299, 399, 200, 800, 0, "url7", "电竞鼠标"),
        ]
        cursor.executemany('''
            INSERT INTO products (id, name, category_id, price, original_price, stock, sales, status, main_image, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', products)

        # 重置自增ID起始值
        cursor.execute("UPDATE sqlite_sequence SET seq=7 WHERE name='products'")
        cursor.execute("UPDATE sqlite_sequence SET seq=2 WHERE name='users'")

        logger.info("测试数据初始化完成")


class DatabaseManager:
    """数据库操作管理器"""

    @staticmethod
    def get_db():
        """获取数据库连接"""
        return get_db()

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_user(username: str, email: str, password: str, phone: str = "") -> int:
        """创建新用户"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password, phone, create_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            return cursor.lastrowid

    @staticmethod
    def get_products(filters: Dict = None) -> List[Dict]:
        """获取商品列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM products WHERE status = 1"
            params = []

            if filters:
                if filters.get('keyword'):
                    query += " AND name LIKE ?"
                    params.append(f"%{filters['keyword']}%")
                if filters.get('category_id'):
                    query += " AND category_id = ?"
                    params.append(filters['category_id'])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Dict]:
        """根据ID获取商品"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_product_stock(product_id: int, quantity: int):
        """更新商品库存"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE products 
                SET stock = stock - ?, sales = sales + ?
                WHERE id = ?
            ''', (quantity, quantity, product_id))

    @staticmethod
    def get_cart_items(user_id: int) -> List[Dict]:
        """获取用户购物车"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, p.name as product_name, p.price as product_price, p.main_image
                FROM carts c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
                ORDER BY c.update_time DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def add_to_cart(user_id: int, product_id: int, quantity: int) -> bool:
        """添加商品到购物车"""
        import time
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 检查是否已存在
            cursor.execute('''
                SELECT * FROM carts WHERE user_id = ? AND product_id = ?
            ''', (user_id, product_id))
            existing = cursor.fetchone()

            if existing:
                cursor.execute('''
                    UPDATE carts 
                    SET quantity = quantity + ?, update_time = ?
                    WHERE user_id = ? AND product_id = ?
                ''', (quantity, now, user_id, product_id))
            else:
                cart_id = f"cart_{int(time.time() * 1000)}"
                cursor.execute('''
                    INSERT INTO carts (cart_id, user_id, product_id, quantity, create_time, update_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (cart_id, user_id, product_id, quantity, now, now))
            return True

    @staticmethod
    def update_cart_quantity(user_id: int, product_id: int, quantity: int) -> bool:
        """更新购物车商品数量"""
        with get_db() as conn:
            cursor = conn.cursor()
            if quantity == 0:
                cursor.execute('''
                    DELETE FROM carts WHERE user_id = ? AND product_id = ?
                ''', (user_id, product_id))
            else:
                cursor.execute('''
                    UPDATE carts 
                    SET quantity = ?, update_time = ?
                    WHERE user_id = ? AND product_id = ?
                ''', (quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, product_id))
            return True

    @staticmethod
    def clear_cart(user_id: int):
        """清空购物车"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))

    @staticmethod
    def add_token_to_blacklist(token: str):
        """添加Token到黑名单"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO token_blacklist (token, create_time)
                VALUES (?, ?)
            ''', (token, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """检查Token是否在黑名单中"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM token_blacklist WHERE token = ?", (token,))
            return cursor.fetchone() is not None


def ensure_database_initialized():
    """确保数据库已初始化（修复 CI 环境问题）"""
    import os
    import sys

    db_path = "ecommerce.db"
    logger.info(f"检查数据库: {os.path.abspath(db_path)}")

    # 检查数据库文件是否存在
    db_exists = os.path.exists(db_path)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            logger.info(f"用户表记录数: {user_count}")

            if user_count == 0:
                logger.info("用户表为空，初始化测试数据...")
                init_test_data()
    except Exception as e:
        logger.warning(f"数据库表可能不存在: {e}")
        logger.info("执行完整初始化...")
        init_database()
        init_test_data()


# 在模块导入时自动执行
ensure_database_initialized()