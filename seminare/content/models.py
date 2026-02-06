from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def path_validator(value):
    if not isinstance(value, str):
        raise ValidationError("Cesta musí byť reťazec.")
    if value.startswith("/") or value.endswith("/"):
        raise ValidationError("Cesta nemôže začínať alebo končit lomítkom.")
    if "//" in value:
        raise ValidationError("Cesta nemôže obsahovať po sebe idúce lomítka.")

    if not all(c.isalnum() or c in "-_/" for c in value):
        raise ValidationError(
            "Cesta môže obsahovať iba alfanumerické znaky, pomlčky, podčiarkovníky a lomítka."
        )


class Page(models.Model):
    id: int
    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    contest_id: int
    slug = models.CharField(validators=[path_validator], max_length=256)
    title = models.CharField(max_length=256)
    content = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint("contest", "slug", name="page__unique_slug")
        ]
        ordering = ["contest", "slug"]

    def __str__(self):
        return self.title


class Post(models.Model):
    id: int
    contests = models.ManyToManyField("contests.Contest", related_name="+")
    slug = models.SlugField(unique=True, max_length=256)
    title = models.CharField(max_length=256)
    content = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class MenuGroup(models.Model):
    id: int
    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    contest_id: int
    title = models.CharField(max_length=256)
    order = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} ({self.contest})"


class MenuItem(models.Model):
    id: int
    group = models.ForeignKey(MenuGroup, on_delete=models.CASCADE)
    group_id: int
    title = models.CharField(max_length=256)
    order = models.IntegerField()
    icon = models.CharField(max_length=256, blank=True)
    url = models.CharField(max_length=256)

    class Meta:
        ordering = ["group", "order"]

    def __str__(self):
        return self.title
