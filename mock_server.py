# mock_server.py
"""
企业级电商Mock服务 - SQLite版本
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import time
from functools import wraps
from datetime import datetime, timedelta
import logging
from common.database import DatabaseManager as DB
from common.database import ensure_database_initialized

# 确保数据库已初始化（修复 CI 环境问题）
ensure_database_initialized()

# ==================== 初始化 ====================
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'ecommerce-mock-secret-2024'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 辅助函数 ====================
def generate_token(user_id):
    """生成JWT Token"""
    user = DB.get_user_by_id(user_id)
    payload = {
        'user_id': user_id,
        'username': user['username'],
        'role': user['role'],
        'exp': datetime.utcnow() + timedelta(hours=2),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token):
    """验证Token"""
    if DB.is_token_blacklisted(token):
        return None
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def token_required(f):
    """Token验证装饰器"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        if token.startswith('Bearer '):
            token = token[7:]

        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': '请先登录'}), 401

        request.user_id = payload['user_id']
        request.user_payload = payload
        return f(*args, **kwargs)

    return decorated


def success_response(data=None, message="success"):
    """成功响应"""
    return jsonify({
        'code': 200,
        'message': message,
        'data': data,
        'timestamp': int(time.time())
    })


def error_response(code, message):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'timestamp': int(time.time())
    }), code


# ==================== 1. 用户模块接口 ====================
@app.route('/api/user/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = DB.get_user_by_username(username)

    if not user or user['password'] != password:
        return error_response(401, '用户名或密码错误')

    if user['status'] != 1:
        return error_response(403, '账号已被禁用')

    token = generate_token(user['id'])

    return success_response({
        'token': token,
        'userInfo': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'phone': user['phone'],
            'role': user['role']
        }
    })


@app.route('/api/user/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone', '')

    if not username or not email or not password:
        return error_response(400, '参数不完整')

    if len(password) < 6:
        return error_response(400, '密码长度不能少于6位')

    # 检查用户名是否存在
    if DB.get_user_by_username(username):
        return error_response(409, '用户名已存在')

    # 创建用户
    user_id = DB.create_user(username, email, password, phone)

    return success_response({'id': user_id, 'username': username}, '注册成功')


@app.route('/api/user/info', methods=['GET'])
@token_required
def get_user_info():
    """获取当前用户信息"""
    user = DB.get_user_by_id(request.user_id)
    if not user:
        return error_response(404, '用户不存在')

    return success_response({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'phone': user['phone'],
        'avatar': user['avatar'],
        'role': user['role'],
        'createTime': user['create_time']
    })


@app.route('/api/user/info', methods=['PUT'])
@token_required
def update_user_info():
    """更新用户信息"""
    # 简化实现，实际需要UPDATE语句
    return success_response({'id': request.user_id}, '更新成功')


@app.route('/api/user/password', methods=['PUT'])
@token_required
def change_password():
    """修改密码"""
    data = request.json
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')

    user = DB.get_user_by_id(request.user_id)
    if user['password'] != old_password:
        return error_response(400, '原密码错误')

    if len(new_password) < 6:
        return error_response(400, '新密码长度不能少于6位')

    # 简化：实际需要UPDATE
    return success_response(None, '密码修改成功')


@app.route('/api/user/logout', methods=['POST'])
@token_required
def logout():
    """退出登录"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    DB.add_token_to_blacklist(token)
    return success_response(None, '退出成功')


# ==================== 2. 商品模块接口 ====================
@app.route('/api/products', methods=['GET'])
def get_products():
    """获取商品列表"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('categoryId', '')
    sort_by = request.args.get('sortBy', 'id')
    sort_order = request.args.get('sortOrder', 'asc')

    # 获取所有商品
    filters = {}
    if keyword:
        filters['keyword'] = keyword
    if category_id:
        filters['category_id'] = int(category_id)

    products = DB.get_products(filters)

    # 排序
    reverse = (sort_order == 'desc')
    if sort_by == 'price':
        products.sort(key=lambda x: x['price'], reverse=reverse)
    elif sort_by == 'sales':
        products.sort(key=lambda x: x['sales'], reverse=reverse)

    # 分页
    total = len(products)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = products[start:end]

    return success_response({
        'list': paginated,
        'total': total,
        'page': page,
        'pageSize': page_size,
        'totalPages': (total + page_size - 1) // page_size
    })


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    """获取商品详情"""
    product = DB.get_product_by_id(product_id)
    if not product:
        return error_response(404, '商品不存在')

    return success_response(product)


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取商品分类"""
    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        categories = [dict(row) for row in cursor.fetchall()]
    return success_response(categories)


# ==================== 3. 购物车模块接口 ====================
@app.route('/api/cart', methods=['GET'])
@token_required
def get_cart():
    """获取购物车"""
    cart_items = DB.get_cart_items(request.user_id)

    # 格式化输出
    result = []
    for item in cart_items:
        result.append({
            'id': item['id'],
            'productId': item['product_id'],
            'productName': item['product_name'],
            'productPrice': item['product_price'],
            'productImage': item['main_image'],
            'quantity': item['quantity'],
            'selected': bool(item['selected']),
            'totalPrice': item['product_price'] * item['quantity']
        })

    total_amount = sum(i['totalPrice'] for i in result if i['selected'])
    selected_count = sum(i['quantity'] for i in result if i['selected'])

    return success_response({
        'list': result,
        'totalAmount': total_amount,
        'selectedCount': selected_count
    })


@app.route('/api/cart/add', methods=['POST'])
@token_required
def add_to_cart():
    """添加商品到购物车"""
    data = request.json
    product_id = data.get('productId')
    quantity = data.get('quantity', 1)

    # 检查商品
    product = DB.get_product_by_id(product_id)
    if not product or product['status'] != 1:
        return error_response(404, '商品不存在或已下架')

    if quantity <= 0:
        return error_response(400, '数量必须大于0')

    DB.add_to_cart(request.user_id, product_id, quantity)

    return success_response(None, '添加成功')


@app.route('/api/cart/update', methods=['PUT'])
@token_required
def update_cart():
    """更新购物车商品数量"""
    data = request.json
    product_id = data.get('productId')
    quantity = data.get('quantity')

    if quantity < 0:
        return error_response(400, '数量不能为负数')

    DB.update_cart_quantity(request.user_id, product_id, quantity)

    return success_response(None, '更新成功')


@app.route('/api/cart/select', methods=['PUT'])
@token_required
def select_cart_item():
    """选中/取消选中购物车商品"""
    data = request.json
    product_id = data.get('productId')
    selected = 1 if data.get('selected', True) else 0

    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE carts SET selected = ?, update_time = ?
            WHERE user_id = ? AND product_id = ?
        ''', (selected, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.user_id, product_id))

    return success_response(None, '更新成功')


@app.route('/api/cart/clear', methods=['DELETE'])
@token_required
def clear_cart():
    """清空购物车"""
    DB.clear_cart(request.user_id)
    return success_response(None, '清空成功')


# ==================== 4. 订单模块接口 ====================
@app.route('/api/orders', methods=['POST'])
@token_required
def create_order():
    """创建订单"""
    data = request.json
    address = data.get('address')
    remark = data.get('remark', '')

    if not address:
        return error_response(400, '请填写收货地址')

    cart_items = DB.get_cart_items(request.user_id)
    selected_items = [item for item in cart_items if item['selected']]

    if not selected_items:
        return error_response(400, '请选择要结算的商品')

    # 计算订单金额并检查库存
    order_items = []
    total_amount = 0

    for item in selected_items:
        product = DB.get_product_by_id(item['product_id'])
        if not product:
            return error_response(400, f'商品{item["product_id"]}不存在')

        if product['stock'] < item['quantity']:
            return error_response(400, f'{product["name"]}库存不足')

        order_items.append({
            'productId': item['product_id'],
            'productName': product['name'],
            'productPrice': product['price'],
            'quantity': item['quantity'],
            'totalPrice': product['price'] * item['quantity']
        })
        total_amount += product['price'] * item['quantity']

    # 扣减库存
    for item in selected_items:
        DB.update_product_stock(item['product_id'], item['quantity'])

    # 清空购物车中已结算的商品
    for item in selected_items:
        DB.update_cart_quantity(request.user_id, item['product_id'], 0)

    # 创建订单
    order_no = f'ORD{datetime.now().strftime("%Y%m%d%H%M%S")}{request.user_id}'
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expire_time = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (order_no, user_id, total_amount, address, remark, create_time, expire_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_no, request.user_id, total_amount, address, remark, create_time, expire_time))

        order_id = cursor.lastrowid

        # 插入订单明细
        for item in order_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity, total_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, item['productId'], item['productName'], item['productPrice'],
                  item['quantity'], item['totalPrice']))

    return success_response({'orderId': order_id, 'orderNo': order_no}, '订单创建成功')


@app.route('/api/orders', methods=['GET'])
@token_required
def get_orders():
    """获取订单列表"""
    status = request.args.get('status', type=int)

    with DB.get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM orders WHERE user_id = ?"
        params = [request.user_id]

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY create_time DESC"
        cursor.execute(query, params)
        orders = [dict(row) for row in cursor.fetchall()]

    return success_response(orders)


@app.route('/api/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order_detail(order_id):
    """获取订单详情"""
    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, request.user_id))
        order = cursor.fetchone()

        if not order:
            return error_response(404, '订单不存在')

        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        items = [dict(row) for row in cursor.fetchall()]

        result = dict(order)
        result['items'] = items

    return success_response(result)


@app.route('/api/orders/<int:order_id>/pay', methods=['POST'])
@token_required
def pay_order(order_id):
    """支付订单"""
    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, request.user_id))
        order = cursor.fetchone()

        if not order:
            return error_response(404, '订单不存在')

        if order['status'] != 0:
            return error_response(400, '订单状态不正确')

        cursor.execute('''
            UPDATE orders 
            SET status = 1, pay_time = ?
            WHERE id = ?
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order_id))

    return success_response({'orderId': order_id, 'status': 'paid'}, '支付成功')


@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@token_required
def cancel_order(order_id):
    """取消订单"""
    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, request.user_id))
        order = cursor.fetchone()

        if not order:
            return error_response(404, '订单不存在')

        if order['status'] not in [0, 1]:
            return error_response(400, '订单状态不允许取消')

        # 恢复库存（无论是否支付，创建订单时都已经扣减了库存）
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        items = cursor.fetchall()
        for item in items:
            # 注意：这里传入正数，因为 update_product_stock 内部是 stock - quantity
            # 要恢复库存，需要传入 -quantity，但这样逻辑混乱
            # 更好的做法：直接修改数据库
            with DB.get_db() as conn2:
                cursor2 = conn2.cursor()
                cursor2.execute('''
                    UPDATE products 
                    SET stock = stock + ?, sales = sales - ?
                    WHERE id = ?
                ''', (item['quantity'], item['quantity'], item['product_id']))

        cursor.execute("UPDATE orders SET status = 4 WHERE id = ?", (order_id,))

    return success_response(None, '取消成功')

@app.route('/api/orders/<int:order_id>/confirm', methods=['POST'])
@token_required
def confirm_order(order_id):
    """确认收货"""
    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, request.user_id))
        order = cursor.fetchone()

        if not order:
            return error_response(404, '订单不存在')

        if order['status'] != 2:
            return error_response(400, '订单状态不正确')

        cursor.execute('''
            UPDATE orders 
            SET status = 3, confirm_time = ?
            WHERE id = ?
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order_id))

    return success_response(None, '确认收货成功')


@app.route('/api/orders/<int:order_id>/ship', methods=['POST'])
@token_required
def ship_order(order_id):
    """发货接口"""
    with DB.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()

        if not order:
            return error_response(404, '订单不存在')

        if order['status'] != 1:
            return error_response(400, '只有已支付的订单才能发货')

        cursor.execute('''
            UPDATE orders 
            SET status = 2, ship_time = ?
            WHERE id = ?
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order_id))

    return success_response(None, '发货成功')


# ==================== 5. 启动服务 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 电商Mock服务启动中 (SQLite版本)...")
    print("💾 数据库文件: ecommerce.db")
    print("=" * 50)
    print("📍 接口地址: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)