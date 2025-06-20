from django.contrib.auth import login, logout
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .serializers import UserLoginSerializer, UserRegistrationSerializer, UserSerializer
from .models import User


class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.

    This endpoint allows new users to create an account by providing
    the necessary registration details.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': 'Registration successful. Please log in.'},
            status=status.HTTP_201_CREATED
        )


class UserLoginView(generics.GenericAPIView):
    """
    API view for user authentication (login).

    This endpoint authenticates a user using their credentials. Upon successful
    validation, it logs the user into the Django session and returns a success message.
    """
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        login(request, user)

        return Response(
            {'message': 'Login successful'},
            status=status.HTTP_200_OK
        )


class ProfileView(generics.RetrieveAPIView):
    """
    API view for retrieving the authenticated user's profile information.

    This endpoint provides access to the current user's details.
    """
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """
    API view for user logout.

    This endpoint logs out the currently authenticated user from the Django session.
    """

    def post(self, request):
        logout(request)
        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )
