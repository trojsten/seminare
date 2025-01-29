from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models


class Page(models.Model):
    id: int
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    site_id: int
    slug = models.SlugField()
    title = models.CharField(max_length=256)
    content = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint("site", "slug", name="page__unique_slug")
        ]
        ordering = ["site", "slug"]

    def __str__(self):
        return self.title


class Post(models.Model):
    contests = models.ManyToManyField("contests.Contest", related_name="+")
    title = models.CharField(max_length=256)
    content = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class MenuGroup(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    order = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} ({self.site})"


class MenuItem(models.Model):
    group = models.ForeignKey(MenuGroup, on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    order = models.IntegerField()
    icon = models.CharField(max_length=256, blank=True)
    url = models.CharField(max_length=256)

    class Meta:
        ordering = ["group", "order"]

    def __str__(self):
        return self.title
