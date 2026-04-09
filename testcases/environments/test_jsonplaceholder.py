"""
JSONPlaceholder 环境独立测试
API 文档: https://jsonplaceholder.typicode.com
"""
import pytest
import allure
from common.api_client import APIClient
from common.assert_helper import AssertHelper


@allure.feature("JSONPlaceholder环境")
class TestJSONPlaceholderEnv:
    """JSONPlaceholder 公开 API 测试"""

    @allure.story("连接测试")
    @allure.title("验证环境可访问")
    def test_environment_reachable(self):
        """测试环境是否可访问"""
        client = APIClient(env="jsonplaceholder")
        response = client.get('/posts/1')
        AssertHelper.assert_status_code(response, 200)
        print("✅ JSONPlaceholder 环境正常")

    @allure.story("帖子接口")
    @allure.title("获取帖子列表")
    def test_get_posts(self):
        """GET /posts - 获取所有帖子"""
        client = APIClient(env="jsonplaceholder")
        response = client.get('/posts')

        AssertHelper.assert_status_code(response, 200)
        posts = response.json()
        assert len(posts) > 0
        assert 'id' in posts[0]
        assert 'title' in posts[0]
        assert 'body' in posts[0]
        assert 'userId' in posts[0]

    @allure.story("帖子接口")
    @allure.title("获取单个帖子")
    def test_get_post_by_id(self):
        """GET /posts/{id} - 获取指定帖子"""
        client = APIClient(env="jsonplaceholder")
        response = client.get('/posts/1')

        AssertHelper.assert_status_code(response, 200)
        post = response.json()
        assert post['id'] == 1
        assert 'title' in post
        assert 'body' in post

    @allure.story("帖子接口")
    @allure.title("获取不存在的帖子")
    def test_get_post_not_exist(self):
        """GET /posts/{id} - 获取不存在的帖子"""
        client = APIClient(env="jsonplaceholder")
        response = client.get('/posts/99999')

        # JSONPlaceholder 返回 404 或空数组
        assert response.status_code in [200, 404]

    @allure.story("用户接口")
    @allure.title("获取用户列表")
    def test_get_users(self):
        """GET /users - 获取所有用户"""
        client = APIClient(env="jsonplaceholder")
        response = client.get('/users')

        AssertHelper.assert_status_code(response, 200)
        users = response.json()
        assert len(users) > 0
        assert 'name' in users[0]
        assert 'email' in users[0]
        assert 'username' in users[0]

    @allure.story("用户接口")
    @allure.title("获取单个用户")
    def test_get_user_by_id(self):
        """GET /users/{id} - 获取指定用户"""
        client = APIClient(env="jsonplaceholder")
        response = client.get('/users/1')

        AssertHelper.assert_status_code(response, 200)
        user = response.json()
        assert user['id'] == 1
        assert user['name'] == "Leanne Graham"

    @allure.story("评论接口")
    @allure.title("获取帖子评论")
    def test_get_comments(self):
        """GET /comments - 获取评论列表"""
        client = APIClient(env="jsonplaceholder")
        response = client.get('/comments?postId=1')

        AssertHelper.assert_status_code(response, 200)
        comments = response.json()
        assert len(comments) > 0
        assert 'name' in comments[0]
        assert 'email' in comments[0]
        assert 'body' in comments[0]

    @allure.story("创建操作")
    @allure.title("创建新帖子")
    def test_create_post(self):
        """POST /posts - 创建新帖子"""
        client = APIClient(env="jsonplaceholder")
        response = client.post('/posts', json={
            'title': 'Test Title',
            'body': 'Test Body',
            'userId': 1
        })

        # JSONPlaceholder 返回 201 Created
        AssertHelper.assert_status_code(response, 201)
        data = response.json()
        assert data['title'] == 'Test Title'
        assert data['body'] == 'Test Body'
        assert data['userId'] == 1
        assert 'id' in data