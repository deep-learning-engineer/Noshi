from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id',  'first_name', 'last_name', 'email', 'phone', 'password')
        write_only_fields = ('password',)
        read_only_fields = ('user_id',)

    def create(self, validated_data):
        user = User.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
        )

        user.set_password(validated_data['password'])
        user.save()

        return user
    