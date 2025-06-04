from django.db import models

from users.models import User


class Achievement(models.Model):
    achievement_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    condition = models.TextField(blank=True)

    class Meta:
        db_table = 'achievements'
        
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='users'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_achievements'
        unique_together = (('achievement', 'user'), )

    def __str__(self):
        return f"{self.user} - {self.achievement} - {self.created_at}"
