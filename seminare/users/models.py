from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Grade(models.TextChoices):
    YOUNG = "YNG", "<5zš"
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


class User(AbstractUser):
    id: int
    trojsten_id = models.BigIntegerField(blank=True, null=True)
    current_school = models.ForeignKey(
        "School", on_delete=models.SET_NULL, blank=True, null=True
    )
    current_school_id: int
    current_grade = models.CharField(choices=Grade.choices, max_length=3, blank=True)

    @property
    def profile_url(self):
        return f"https://id.trojsten.sk/profile/{self.username}/"

    @property
    def avatar_url(self):
        return f"https://id.trojsten.sk/profile/{self.username}/avatar/"

    @property
    def display_name(self):
        if self.first_name and self.last_name:
            return self.get_full_name()
        return self.username


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
    problem_set = models.ForeignKey("problems.ProblemSet", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, blank=True, null=True)
    grade = models.CharField(choices=Grade.choices, max_length=3)

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


class ContestRole(models.Model):
    class Role(models.IntegerChoices):
        ORGANIZER = 1
        ADMINISTRATOR = 2

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_id: int
    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    contest_id: int
    role = models.IntegerField(choices=Role.choices)

    def __str__(self):
        return f"{self.user}, {self.contest}: {self.get_role_display()}"

    def get_role_display(self) -> str:
        return self.get_role_display()
