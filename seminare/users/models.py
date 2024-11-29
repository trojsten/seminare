from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models


class User(AbstractUser, PermissionsMixin):
    category = models.IntegerField(blank=True, null=True)
