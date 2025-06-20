from rest_framework import serializers
from .models import UserAchievement


class UserAchievementSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="achievement.name")
    condition = serializers.CharField(source="achievement.condition")

    class Meta:
        model = UserAchievement
        fields = ("created_at", "name", "condition")
