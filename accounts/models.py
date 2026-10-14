from django.contrib.auth.models import AbstractUser
from django.db import models


class SubscriptionStatus(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "subscription status"
        verbose_name_plural = "subscription statuses"
        ordering = ("name",)

    def __str__(self):
        return self.name


class User(AbstractUser):
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True)
    status = models.ForeignKey(
        SubscriptionStatus,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="users",
    )
    bio = models.TextField(blank=True)
