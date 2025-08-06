from django.db import models


class OldRound(models.Model):
    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    old_round_id = models.IntegerField()
    problem_set = models.ForeignKey(
        "problems.ProblemSet", on_delete=models.CASCADE, related_name="+"
    )
    problem_set_id: int

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "contest", "old_round_id", name="oldround_contest_round_unique"
            ),
        ]

    def __str__(self) -> str:
        return f"Round #{self.old_round_id}"


class OldProblem(models.Model):
    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    old_problem_id = models.IntegerField()
    problem = models.ForeignKey(
        "problems.Problem", on_delete=models.CASCADE, related_name="+"
    )
    problem_id: int

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "contest", "old_problem_id", name="oldproblem_contest_problem_unique"
            ),
        ]

    def __str__(self) -> str:
        return f"Problem #{self.old_problem_id}"
