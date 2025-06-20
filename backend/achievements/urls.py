from django.urls import path
from .views import UserAchievementsListView

urlpatterns = [
    path("achievements/", UserAchievementsListView.as_view(), name="user-achievements"),
]
