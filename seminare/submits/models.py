import os
import secrets

from django.conf import settings
from django.db import models


def submit_file_filepath(instance: "BaseSubmit", filename):
    _, ext = os.path.splitext(filename)
    rnd_str = secrets.token_hex(8)
    return f"submits/{instance.problem_id}/{instance.enrollment.user_id}_{rnd_str}{ext}"


class BaseSubmit(models.Model):
    id: int
    enrollment = models.ForeignKey("users.Enrollment", on_delete=models.CASCADE)
    enrollment_id: int
    problem = models.ForeignKey("problems.Problem", on_delete=models.CASCADE)
    problem_id: int
    created_at = models.DateTimeField(auto_now_add=True)

    score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    scored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    scored_by_id: int
    comment = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.problem} ({self.enrollment.user})"

    @property
    def submit_id(self):
        raise NotImplementedError()

    @classmethod
    def get_submit_by_id(cls, submit_id: str) -> "BaseSubmit|None":
        try:
            submit_type, id = submit_id.split("-", 1)
        except ValueError:
            return None

        submit_types = {
            "F": FileSubmit,
            "J": JudgeSubmit,
            "T": TextSubmit,
        }
        if submit_type not in submit_types:
            return None

        if not id.isnumeric():
            return None

        return submit_types[submit_type].objects.filter(id=id).first()


class FileSubmit(BaseSubmit):
    file = models.FileField(upload_to=submit_file_filepath)
    comment_file = models.FileField(upload_to=submit_file_filepath, blank=True)

    @property
    def submit_id(self):
        return f"F-{self.id}"


class JudgeSubmit(BaseSubmit):
    program = models.TextField(blank=True)
    protocol = models.JSONField(blank=True, default=dict)
    judge_id = models.CharField(max_length=255, unique=True)
    protocol_key = models.CharField(max_length=255, blank=True)

    @property
    def submit_id(self):
        return f"J-{self.id}"


class TextSubmit(BaseSubmit):
    value = models.TextField(blank=True)

    @property
    def submit_id(self):
        return f"T-{self.id}"
