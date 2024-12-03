from django.db import models

from seminare.problems.models import Problem
from seminare.users.models import Enrollment


def submit_file_file(instance, filename):
    return "didky"


class Submit(models.Model):
    class SubmitTypes(models.TextChoices):
        PROGRAM = "PR", "Program"
        DESCRIPTION = "DE", "Description"
        SUSI = "SU", "Susi"

    created_at = models.DateField(auto_now_add=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    type = models.CharField(choices=SubmitTypes)
    score = models.FloatField(default=0)
    graded = models.BooleanField()
    protocol = models.TextField(blank=True)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    file = models.FileField(upload_to=submit_file_file)

    class Meta:
        ordering = ["created_at", "score"]

    def __str__(self):
        return f"{self.problem}({self.enrollment.user}) - {self.created_at}"
