from django.db import models


class ProblemSet(models.Model):
    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    name = models.CharField(blank=True, max_length=256)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["start_date", "end_date"]

    def __str__(self):
        return self.name


class Problem(models.Model):
    name = models.CharField(blank=True, max_length=256)
    number = models.IntegerField(default=0)
    problem_set = models.ForeignKey(ProblemSet, on_delete=models.CASCADE)

    class Meta:
        ordering = ["problem_set", "number"]

    def __str__(self):
        return f"{self.name}({self.number})"


class Text(models.Model):
    class Type(models.TextChoices):
        PROBLEM_STATEMENT = "PS", "Problem statement"
        EXAMPLE_SOLUTION = "ES", "Example solution"
        SUSI_SMALL_HINT = "SSH", "Susi small hint"
        SUSI_LARGE_HINT = "SLH", "Susi large hint"

    text = models.TextField(blank=True)
    type = models.CharField(choices=Type)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    class Meta:
        ordering = ["problem", "type"]

    def __str__(self):
        return f"{self.problem}({self.type})"
