from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from typing import Tuple

from testutils import faker
from testutils import get_user_or_create, set_allow_register


class AuthTest(APITestCase):

    def login(self, password='testpassword') -> Tuple[User, Response]:
        url = reverse('login')
        user = get_user_or_create(username=faker.name(), password=password)
        data = {'username': user.username, 'password': password}
        return user, self.client.post(url, data)

    def register(self, username: str, password: str) -> Response:
        url = reverse('register')
        data = {'username': username, 'password': password}
        response = self.client.post(url, data)
        return response

    def test_login(self):
        user, response = self.login()
        token = Token.objects.get(user=user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())
        self.assertEqual(token.key, response.json()['token'])
        
    def test_logout(self):
        user, login_response = self.login()
        old_token = login_response.json()['token']

        url = reverse('logout')
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {old_token}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Token.DoesNotExist):
            Token.objects.get(user=user)

    def test_not_allow_register(self):
        set_allow_register(False)
        user_info = {
            'username': faker.user_name(),
            'password': faker.password(),
        }
        response = self.register(
            username=user_info['username'],
            password=user_info['password']
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_register(self):
        set_allow_register(True)

        username = faker.user_name()
        password = faker.password()

        response = self.register(username=username, password=password)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username=username)
        self.assertTrue(user.check_password(password))
