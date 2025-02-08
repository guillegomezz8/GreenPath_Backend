from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from ..models import User

class APITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        data = {
            'username': 'testUser2',
            'password': 'password',
            'email': 'user2@example.com',
            'name': 'test2',
            'last_name': 'user2'
        }

        url = '/users/'
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.all()[0].name, 'test2')

    def test_retrieve_user(self):
        user = User.objects.create_user(
            username='testUser2',
            password='password',
            email='user2@example.com',
            name='test2',
            last_name='user2'
        )

        url = f'/users/{user.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user(self):
        user = User.objects.create_user(
            username='testUser2',
            password='password',
            email='user2@example.com',
            name='test2',
            last_name='user2'
        )

        data = {
            'username': 'testUserUpdate',
            'password': 'password',
            'email': 'userUpdate@example.com',
            'name': 'testUpdate',
            'last_name': 'userUpdate'
        }

        url = f'/users/{user.id}/'        
        response = self.client.put(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_user(self):
        user = User.objects.create_user(
            username='testUser2',
            password='password',
            email='user2@example.com',
            name='test2',
            last_name='user2'
        )

        data = {
            'username': 'testUserUpdate',
        }      
        
        url = f'/users/{user.id}/'
        response = self.client.patch(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_user(self):
        user = User.objects.create_user(
            username='testUser2',
            password='password',
            email='user2@example.com',
            name='test2',
            last_name='user2'
        )        
        
        url = f'/users/{user.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)