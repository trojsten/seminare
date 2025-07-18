from datetime import datetime

from django.db import models

from seminare.users.models import ContestRole, User


class ContestQuerySet(models.QuerySet):
    def for_admin(
        self, user: User, require_role: ContestRole.Role = ContestRole.Role.ORGANIZER
    ):
        if user.is_superuser:
            return self

        contests = ContestRole.objects.filter(
            user=user, role__gte=require_role
        ).values_list("contest_id", flat=True)
        return self.filter(id__in=contests)


class Contest(models.Model):
    id: int
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50)
    site = models.OneToOneField("sites.Site", on_delete=models.CASCADE)
    site_id: int

    objects = ContestQuerySet.as_manager()

    def __str__(self):
        return self.name

    @property
    def theme_name(self):
        return f"theme-{self.short_name.lower()}"

    @property
    def logo_path(self):
        return f"/static/contests/{self.short_name.lower()}/logo.svg"


class RuleDataQuerySet(models.QuerySet):
    def for_contest(
        self,
        contest: Contest,
        effective_date: datetime | None = None,
        engines: list[str] | None = None,
    ):
        if effective_date is None:
            effective_date = datetime.now()

        qs = self.filter(contest=contest, created_at__lte=effective_date)

        if engines is not None:
            qs = qs.filter(engine__in=engines)

        return qs.order_by("user", "-created_at").distinct("user")

    def for_users(
        self,
        contest: Contest,
        users: list[User],
        effective_date: datetime | None = None,
        engines: list[str] | None = None,
    ):
        if effective_date is None:
            effective_date = datetime.now()

        qs = self.filter(
            contest=contest, user__in=users, created_at__lte=effective_date
        )

        if engines is not None:
            qs = qs.filter(engine__in=engines)

        return qs.order_by("user", "-created_at").distinct("user")

    def for_user(
        self,
        contest: Contest,
        user: User,
        effective_date: datetime | None = None,
        engines: list[str] | None = None,
    ):
        if effective_date is None:
            effective_date = datetime.now()

        qs = self.filter(contest=contest, user=user, created_at__lte=effective_date)

        if engines is not None:
            qs = qs.filter(engine__in=engines)

        return qs.order_by("-created_at").first()


class RuleData(models.Model):
    id: int

    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name="rule_data",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="rule_data",
    )
    engine = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField()

    objects = RuleDataQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contest} - {self.user} - {self.engine} ({self.created_at})"
