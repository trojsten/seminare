from django.db import models


class Camp(models.Model):
    id: int

    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    is_finalized = models.BooleanField(default=False)

    problem_set = models.ForeignKey(
        "problems.ProblemSet",
        on_delete=models.RESTRICT,
        related_name="camps",
    )
    problem_set_id: int

    attendees: models.QuerySet["CampAttendee"]

    def __str__(self):
        return self.name


class CampAttendee(models.Model):
    id: int

    camp = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name="attendees")
    camp_id: int

    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="camps_attended",
        blank=True,
        null=True,
    )
    user_id: int
    name = models.CharField(max_length=100, blank=True, default="")

    is_organizer = models.BooleanField(default=False)

    class Meta:
        unique_together = ("camp", "user")

    def __str__(self):
        return f"{self.user} attending {self.camp}"
