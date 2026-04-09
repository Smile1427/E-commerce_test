"""
购物车模块测试用例 - （含数据库验证）
"""
import pytest
import allure
from common.assert_helper import AssertHelper


@allure.feature("购物车模块")
class TestCart:

    @allure.story("购物车操作")
    @allure.title("测试添加商品到购物车")
    def test_add_to_cart(self, api_client, auth_token, clean_cart, db_verifier, get_current_user_id):
        """测试添加商品到购物车"""
        # 添加商品
        response = api_client.post('/api/cart/add', json={
            'productId': 1,
            'quantity': 2
        })

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        # API验证
        cart_response = api_client.get('/api/cart')
        cart_data = cart_response.json()['data']
        assert len(cart_data['list']) > 0

        # 数据库验证
        user_id = get_current_user_id
        cart_items = db_verifier.get_cart_items(user_id)
        assert len(cart_items) == 1
        assert cart_items[0]['product_id'] == 1
        assert cart_items[0]['quantity'] == 2
        assert cart_items[0]['selected'] == 1

    @allure.story("购物车操作")
    @allure.title("测试添加重复商品（应增加数量）")
    def test_add_duplicate_product(self, api_client, auth_token, clean_cart, db_verifier, get_current_user_id):
        """测试重复添加同一商品"""
        # 第一次添加
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 1})
        # 第二次添加
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 2})

        # API验证
        response = api_client.get('/api/cart')
        cart_data = response.json()['data']
        item = next((i for i in cart_data['list'] if i['productId'] == 1), None)
        assert item is not None
        assert item['quantity'] == 3

        # 数据库验证
        user_id = get_current_user_id
        cart_items = db_verifier.get_cart_items(user_id)
        assert len(cart_items) == 1
        assert cart_items[0]['quantity'] == 3

    @allure.story("购物车操作")
    @allure.title("测试更新购物车商品数量")
    def test_update_cart_quantity(self, api_client, auth_token, clean_cart, db_verifier, get_current_user_id):
        """测试更新购物车商品数量"""
        # 先添加商品
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 2})

        # 更新数量
        response = api_client.put('/api/cart/update', json={
            'productId': 1,
            'quantity': 5
        })
        AssertHelper.assert_status_code(response, 200)

        # API验证
        cart_response = api_client.get('/api/cart')
        item = next(i for i in cart_response.json()['data']['list'] if i['productId'] == 1)
        assert item['quantity'] == 5

        # 数据库验证
        user_id = get_current_user_id
        cart_items = db_verifier.get_cart_items(user_id)
        assert cart_items[0]['quantity'] == 5

    @allure.story("购物车操作")
    @allure.title("测试删除购物车商品（数量设为0）")
    def test_remove_from_cart(self, api_client, auth_token, clean_cart, db_verifier, get_current_user_id):
        """测试删除购物车商品"""
        # 添加商品
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 2})

        # 删除（数量设为0）
        response = api_client.put('/api/cart/update', json={
            'productId': 1,
            'quantity': 0
        })
        AssertHelper.assert_status_code(response, 200)

        # API验证
        cart_response = api_client.get('/api/cart')
        found = any(i['productId'] == 1 for i in cart_response.json()['data']['list'])
        assert not found

        # 数据库验证：购物车为空
        user_id = get_current_user_id
        cart_count = db_verifier.get_cart_count(user_id)
        assert cart_count == 0

    @allure.story("购物车操作")
    @allure.title("测试清空购物车")
    def test_clear_cart(self, api_client, auth_token, db_verifier, get_current_user_id):
        """测试清空购物车"""
        # 添加多个商品
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 1})
        api_client.post('/api/cart/add', json={'productId': 2, 'quantity': 1})

        # 清空
        response = api_client.delete('/api/cart/clear')
        AssertHelper.assert_status_code(response, 200)

        # API验证
        cart_response = api_client.get('/api/cart')
        assert len(cart_response.json()['data']['list']) == 0

        # 数据库验证
        user_id = get_current_user_id
        cart_count = db_verifier.get_cart_count(user_id)
        assert cart_count == 0

    @allure.story("购物车操作")
    @allure.title("测试选中/取消选中商品")
    def test_select_cart_item(self, api_client, auth_token, clean_cart, db_verifier, get_current_user_id):
        """测试选中/取消选中商品"""
        # 添加商品
        api_client.post('/api/cart/add', json={'productId': 1, 'quantity': 2})

        # 取消选中
        response = api_client.put('/api/cart/select', json={
            'productId': 1,
            'selected': False
        })
        AssertHelper.assert_status_code(response, 200)

        # API 验证：总金额为0（因为未选中）
        cart_response = api_client.get('/api/cart')
        assert cart_response.json()['data']['totalAmount'] == 0

        # 数据库验证：selected 字段已更新为 0
        user_id = get_current_user_id
        cart_items = db_verifier.get_cart_items(user_id)
        assert len(cart_items) == 1
        assert cart_items[0]['selected'] == 0

        # 重新选中
        response = api_client.put('/api/cart/select', json={
            'productId': 1,
            'selected': True
        })
        AssertHelper.assert_status_code(response, 200)

        # 验证总金额恢复
        cart_response = api_client.get('/api/cart')
        assert cart_response.json()['data']['totalAmount'] > 0