from django.conf import settings
from django.db import models


class ProblemSet(models.Model):
    name = models.fields.CharField(max_length=64)
    deadline = models.fields.DateField()

    def __str__(self):
        return self.name


class Problem(models.Model):
    name = models.fields.CharField(max_length=64)
    content = models.fields.TextField(blank=True)
    category = models.fields.IntegerField()
    max_score = models.fields.FloatField(default=20)
    problem_set = models.ForeignKey(
        ProblemSet, on_delete=models.CASCADE, related_name="problems"
    )

    def __str__(self):
        return self.name


class Submit(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    score = models.fields.FloatField()
    file = models.FileField(blank=True)

    def __str__(self):
        return f"{self.created_at.strftime("%d-%m-%Y, %H:%M:%S")} - {self.score}"
