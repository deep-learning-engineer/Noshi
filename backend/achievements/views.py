from rest_framework import generics, permissions
from .models import UserAchievement
from .serializers import UserAchievementSerializer


class UserAchievementsListView(generics.ListAPIView):
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (UserAchievement.objects
                .filter(user=self.request.user)
                .select_related("achievement")
                .order_by("-created_at"))
