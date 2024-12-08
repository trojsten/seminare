from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class School(models.Model):
    name = models.CharField(blank=True, max_length=256)
    short_name = models.CharField(blank=True, max_length=64)
    edu_id = models.CharField(unique=True, max_length=16)
    address = models.CharField(blank=True, max_length=256)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.short_name


class Enrollment(models.Model):
    class Grade(models.TextChoices):
        ZS5 = "5ZS", "5zš"
        ZS6 = "6ZS", "6zš"
        ZS7 = "7ZS", "7zš"
        ZS8 = "8ZS", "8zš"
        ZS9 = "9ZS", "9zš"
        SS1 = "1SS", "1"
        SS2 = "2SS", "2"
        SS3 = "3SS", "3"
        SS4 = "4SS", "4"
        SS5 = "5SS", "5"
        OLD = "OLD", "∞"

    problem_set = models.ForeignKey("problems.ProblemSet", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    grade = models.CharField(choices=Grade)
    category = models.ForeignKey("contests.Category", on_delete=models.CASCADE)

    class Meta:
        ordering = ["problem_set", "user"]
        constraints = [
            models.UniqueConstraint(
                fields=("user", "problem_set"),
                name="enrollment_unique__user_problemset",
            ),
        ]

    def __str__(self):
        return f"{self.user} ({self.grade})"
