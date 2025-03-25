import pytest

from .serializers import UserSerializer


@pytest.fixture
def user_data():
    return {
        'first_name': 'Tim',
        'last_name': 'Ilon',
        'email': 'tim@mail.com',
        'phone': '7921231212'
    }
    
    
@pytest.mark.django_db
def test_user_serialization_create(user_data):
    serializer = UserSerializer(data=user_data)
    
    assert serializer.is_valid()
    assert serializer.data == user_data
    