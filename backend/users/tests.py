import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    return User.objects.create_user(
        email='testuser@example.com',
        password='testpass123',
        phone='79999999999',
        first_name='Test',
        last_name='User'
    )


@pytest.mark.django_db
class TestUserRegistrationView:
    url = reverse('register')
    
    def test_successful_registration(self, api_client):
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'phone':'79999999999'
        }
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='newuser@example.com').exists()
        
    def test_registration_with_existing_email(self, api_client, test_user):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
        }
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        
    def test_registration_with_missing_fields(self, api_client):
        data = {
            'email': 'incomplete@example.com',
            'password': 'testpass123',
        }
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'first_name' in response.data
        assert 'last_name' in response.data


@pytest.mark.django_db
class TestUserLoginView:
    url = reverse('login')
    
    def test_successful_login(self, api_client, test_user):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123',
        }
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK

    def test_login_with_wrong_password(self, api_client, test_user):
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword',
        }
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        
    def test_login_with_nonexistent_email(self, api_client):
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123',
        }
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        
    def test_login_with_missing_credentials(self, api_client):
        data = {}
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        assert 'password' in response.data
        