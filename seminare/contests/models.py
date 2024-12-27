from django.db import models
from django.db.models import UniqueConstraint


class Contest(models.Model):
    id: int
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50)
    site = models.ForeignKey("sites.Site", on_delete=models.CASCADE)
    site_id: int
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=256)
    identifier = models.CharField(max_length=128)
    contest = models.ForeignKey("Contest", on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]
        constraints = [
            UniqueConstraint(
                "contest", "identifier", name="unique__category_identifier"
            ),
        ]

    def __str__(self):
        return self.name
