from datetime import date
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


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

    @classmethod
    def is_old(cls, grade: str, is_prask=False) -> bool:
        old_grades = {cls.OLD}

        if is_prask:
            old_grades |= {cls.SS2, cls.SS3, cls.SS4, cls.SS5}

        return grade in old_grades

    @classmethod
    def is_ss(cls, grade: str) -> bool:
        return grade.startswith("SS")


class User(AbstractUser):
    id: int
    trojsten_id = models.BigIntegerField(blank=True, null=True)
    current_school = models.ForeignKey(
        "School", on_delete=models.SET_NULL, blank=True, null=True
    )
    current_school_id: int
    current_grade = models.CharField(choices=Grade.choices, max_length=3, blank=True)

    enrollment_set: "RelatedManager[Enrollment]"

    objects: "UserManager[User]"

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

    def update_school_info(self, school_info: dict | None):
        from seminare.users.logic.schools import get_grade_from_type_year

        if not school_info:
            self.current_school = None
            self.current_grade = ""
            return

        end_date = school_info["end_date"]
        is_expired = end_date and date.fromisoformat(end_date) < date.today()
        if is_expired:
            self.current_school = None
            self.current_grade = ""
            return

        school_data = school_info["school"]
        school, _ = School.objects.get_or_create(
            edu_id=school_data["eduid"],
            defaults={
                "name": school_data["name"],
                "address": school_data["address"],
            },
        )
        self.current_school = school

        school_type = school_info["school_type"]
        current_year = int(school_info["current_year"])
        self.current_grade = get_grade_from_type_year(school_type, current_year) or ""


class School(models.Model):
    name = models.CharField(blank=True, max_length=256)
    short_name = models.CharField(blank=True, max_length=64)
    edu_id = models.CharField(unique=True, blank=True, null=True, max_length=16)
    address = models.CharField(blank=True, max_length=256)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.address}"


class Enrollment(models.Model):
    id: int

    problem_set = models.ForeignKey("problems.ProblemSet", on_delete=models.CASCADE)
    problem_set_id: int
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_id: int
    school = models.ForeignKey(School, on_delete=models.CASCADE, blank=True, null=True)
    school_id: int
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
        return f"{self.user} - {self.problem_set} ({self.grade})"


class ContestRole(models.Model):
    class Role(models.IntegerChoices):
        ORGANIZER = 1, "Organizátor"
        ADMINISTRATOR = 2, "Administrátor"

    id: int
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_id: int
    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    contest_id: int
    role = models.IntegerField(choices=Role.choices)

    def __str__(self):
        return f"{self.user}, {self.contest}: {self.get_role_display()}"

    if TYPE_CHECKING:

        def get_role_display(self) -> str: ...
