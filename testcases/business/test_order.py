"""
订单模块测试用例 - （含数据库验证）
"""
import pytest
import allure
from common.assert_helper import AssertHelper


@allure.feature("订单模块")
class TestOrder:

    @allure.story("创建订单")
    @allure.title("测试正常创建订单")
    def test_create_order_success(self, api_client, auth_token, clean_cart, db_verifier, get_current_user_id):
        """测试正常创建订单 - 验证数据库状态"""
        # 先添加商品到购物车
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 2})

        # 记录商品原库存
        original_stock = db_verifier.get_product_stock(1)
        original_sales = db_verifier.get_product_sales(1)

        # 创建订单
        response = api_client.post('/api/orders', json={
            'address': '测试地址 123号'
        })

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        data = response.json()['data']
        order_id = data['orderId']

        # 数据库验证：订单已创建
        order = db_verifier.get_order_by_id(order_id)
        assert order is not None
        assert order['user_id'] == get_current_user_id
        assert order['address'] == '测试地址 123号'
        assert order['status'] == 0  # 待支付
        assert order['total_amount'] == 6499 * 2  # 商品1的价格是6499

        # 验证订单明细
        order_items = db_verifier.get_order_items(order_id)
        assert len(order_items) == 1
        assert order_items[0]['product_id'] == 1
        assert order_items[0]['quantity'] == 2
        assert order_items[0]['total_price'] == 6499 * 2

        # 验证库存已扣减
        new_stock = db_verifier.get_product_stock(1)
        new_sales = db_verifier.get_product_sales(1)
        assert new_stock == original_stock - 2
        assert new_sales == original_sales + 2

        # 验证购物车已清空（已结算商品被删除）
        cart_count = db_verifier.get_cart_count(get_current_user_id)
        assert cart_count == 0

    @allure.story("创建订单")
    @allure.title("测试未选择商品时创建订单失败")
    def test_create_order_empty_cart(self, api_client, auth_token, clean_cart):
        """测试购物车为空时创建订单"""
        response = api_client.post('/api/orders', json={
            'address': '测试地址'
        })

        AssertHelper.assert_status_code(response, 400)
        AssertHelper.assert_business_code(response, 400)

    @allure.story("创建订单")
    @allure.title("测试未填写地址时创建订单失败")
    def test_create_order_no_address(self, api_client, auth_token, clean_cart):
        """测试未填写地址"""
        # 先添加商品到购物车
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 1})

        # 不传 address 参数
        response = api_client.post('/api/orders', json={})

        AssertHelper.assert_status_code(response, 400)
        AssertHelper.assert_business_code(response, 400)

    @allure.story("订单支付")
    @allure.title("测试支付订单")
    def test_pay_order(self, api_client, auth_token, clean_cart, db_verifier):
        """测试支付订单 - 验证数据库状态更新"""
        # 创建订单
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 1})
        order_response = api_client.post('/api/orders', json={'address': '测试地址'})
        order_id = order_response.json()['data']['orderId']

        # 支付
        response = api_client.post(f'/api/orders/{order_id}/pay')
        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        # API验证
        order_detail = api_client.get(f'/api/orders/{order_id}')
        assert order_detail.json()['data']['status'] == 1

        # 数据库验证：订单状态已更新
        order = db_verifier.get_order_by_id(order_id)
        assert order['status'] == 1
        assert order['pay_time'] is not None

    @allure.story("订单取消")
    @allure.title("测试取消未支付订单")
    def test_cancel_order(self, api_client, auth_token, clean_cart, db_verifier):
        """测试取消未支付订单 - 验证库存恢复"""
        # 记录原库存
        original_stock = db_verifier.get_product_stock(1)

        # 创建订单
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 1})
        order_response = api_client.post('/api/orders', json={'address': '测试地址'})
        order_id = order_response.json()['data']['orderId']

        # 验证库存已扣减
        assert db_verifier.get_product_stock(1) == original_stock - 1

        # 取消订单
        response = api_client.post(f'/api/orders/{order_id}/cancel')
        AssertHelper.assert_status_code(response, 200)

        # 数据库验证：订单状态已取消
        order = db_verifier.get_order_by_id(order_id)
        assert order['status'] == 4

        # 验证库存已恢复（未支付订单取消应恢复库存）
        assert db_verifier.get_product_stock(1) == original_stock

    @allure.story("订单状态流转")
    @allure.title("测试完整订单流程")
    def test_order_full_flow(self, api_client, auth_token, clean_cart, db_verifier):
        """测试完整订单流程：下单→支付→发货→确认收货"""
        # 1. 创建订单
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 1})
        order_response = api_client.post('/api/orders', json={'address': '测试地址'})
        order_id = order_response.json()['data']['orderId']

        # 验证状态：待支付
        assert db_verifier.get_order_by_id(order_id)['status'] == 0

        # 2. 支付
        api_client.post(f'/api/orders/{order_id}/pay')
        assert db_verifier.get_order_by_id(order_id)['status'] == 1

        # 3. 发货
        api_client.post(f'/api/orders/{order_id}/ship')
        assert db_verifier.get_order_by_id(order_id)['status'] == 2

        # 4. 确认收货
        response = api_client.post(f'/api/orders/{order_id}/confirm')
        AssertHelper.assert_status_code(response, 200)

        # 最终验证：订单已完成
        order = db_verifier.get_order_by_id(order_id)
        assert order['status'] == 3
        assert order['confirm_time'] is not None