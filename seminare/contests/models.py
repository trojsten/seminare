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
