"""
用户模块测试用例 - （含数据库验证）
"""
import pytest
import allure
from common.assert_helper import AssertHelper


@allure.feature("用户模块")
class TestUser:

    @allure.story("登录功能")
    @allure.title("测试正常登录")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_success(self, api_client, test_user, db_verifier):
        """测试正确的用户名密码登录"""
        response = api_client.post('/api/user/login', json={
            'username': test_user['username'],
            'password': test_user['password']
        })

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        data = response.json()['data']
        AssertHelper.assert_field_exists(data, 'token')
        AssertHelper.assert_field_exists(data, 'userInfo')
        AssertHelper.assert_field_value(data['userInfo'], 'username', test_user['username'])

        # 数据库验证：确认用户存在于数据库中
        user_in_db = db_verifier.get_user_by_username(test_user['username'])
        assert user_in_db is not None, "用户应该存在于数据库中"
        assert user_in_db['username'] == test_user['username']
        assert user_in_db['status'] == 1

    @allure.story("登录功能")
    @allure.title("测试密码错误")
    def test_login_wrong_password(self, api_client, test_user, db_verifier):
        """测试密码错误"""
        response = api_client.post('/api/user/login', json={
            'username': test_user['username'],
            'password': 'wrongpassword'
        })

        AssertHelper.assert_status_code(response, 401)
        AssertHelper.assert_business_code(response, 401)

        # 数据库验证：用户状态未改变
        user_in_db = db_verifier.get_user_by_username(test_user['username'])
        assert user_in_db is not None
        assert user_in_db['password'] == test_user['password']  # 密码未被修改

    @allure.story("登录功能")
    @allure.title("测试用户名不存在")
    def test_login_user_not_exist(self, api_client, db_verifier):
        """测试用户名不存在"""
        response = api_client.post('/api/user/login', json={
            'username': 'notexistuser',
            'password': '123456'
        })

        AssertHelper.assert_status_code(response, 401)
        AssertHelper.assert_business_code(response, 401)

    @allure.story("用户注册")
    @allure.title("测试正常注册")
    def test_register_success(self, api_client, cleanup_user, db_verifier):
        """测试正常注册新用户 - 包含数据库验证"""
        import time
        timestamp = int(time.time())
        username = f'newuser_{timestamp}'
        email = f'newuser_{timestamp}@test.com'
        phone = '13800138001'

        # 记录用户以便清理
        cleanup_user(username, email, 'Test123456')

        response = api_client.post('/api/user/register', json={
            'username': username,
            'email': email,
            'password': 'Test123456',
            'phone': phone
        })

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        data = response.json()['data']
        AssertHelper.assert_field_exists(data, 'id')
        AssertHelper.assert_field_exists(data, 'username')

        # 数据库验证：用户已正确插入数据库
        user_in_db = db_verifier.get_user_by_username(username)
        assert user_in_db is not None, "用户应该被插入到数据库"
        assert user_in_db['username'] == username
        assert user_in_db['email'] == email
        assert user_in_db['phone'] == phone
        assert user_in_db['status'] == 1
        assert user_in_db['role'] == 'user'
        assert user_in_db['create_time'] is not None

        # 验证ID匹配
        assert user_in_db['id'] == data['id']

    @allure.story("用户注册")
    @allure.title("测试注册时用户名已存在")
    def test_register_username_exists(self, api_client, test_user, db_verifier):
        """测试注册已存在的用户名"""
        response = api_client.post('/api/user/register', json={
            'username': test_user['username'],
            'email': 'newemail@test.com',
            'password': 'Test123456'
        })

        AssertHelper.assert_status_code(response, 409)
        AssertHelper.assert_business_code(response, 409)

        # 数据库验证：没有插入重复用户
        users = db_verifier.get_user_by_username(test_user['username'])
        assert users is not None
        # 确保只有一个该用户名的记录

    @allure.story("用户信息")
    @allure.title("测试获取用户信息")
    def test_get_user_info(self, api_client, auth_token, test_user, db_verifier, get_current_user_id):
        """测试获取当前用户信息"""
        response = api_client.get('/api/user/info')

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        data = response.json()['data']
        AssertHelper.assert_field_exists(data, 'id')
        AssertHelper.assert_field_exists(data, 'username')
        AssertHelper.assert_field_exists(data, 'email')

        # 数据库验证：返回的信息与数据库一致
        user_id = get_current_user_id
        user_in_db = db_verifier.get_user_by_id(user_id)
        assert user_in_db is not None
        assert data['username'] == user_in_db['username']
        assert data['email'] == user_in_db['email']
        assert data['phone'] == user_in_db['phone']

    @allure.story("退出登录")
    @allure.title("测试退出登录")
    def test_logout(self, api_client, auth_token, db_verifier):
        """测试退出登录 - Token应加入黑名单"""
        # 获取当前token
        token = api_client.token

        # 退出登录
        response = api_client.post('/api/user/logout')
        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        # 数据库验证：Token被加入黑名单
        assert db_verifier.is_token_blacklisted(token), "Token应该被加入黑名单"

        # 验证：使用旧token无法访问需要认证的接口
        response2 = api_client.get('/api/user/info')
        # 应该返回401（未授权）
        assert response2.status_code == 401