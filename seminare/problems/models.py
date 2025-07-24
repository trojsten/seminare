from datetime import datetime, time
from typing import TYPE_CHECKING, TypedDict

from django.db import models
from django.db.models import UniqueConstraint
from django.urls import reverse
from django.utils import timezone

from seminare.rules import RuleEngine, get_rule_engine_class
from seminare.submits.models import BaseSubmit

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


class ProblemSetQuerySet(models.QuerySet):
    def for_user(self, user):
        # TODO: real permission check
        return self.filter(is_public=True)

    def only_current(self):
        return self.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())


class ProblemSet(models.Model):
    id: int

    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    contest_id: int

    name = models.CharField(max_length=256)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    is_public = models.BooleanField(default=False)

    rule_engine = models.CharField(max_length=512)
    rule_engine_options = models.JSONField(default=dict, blank=True)

    objects = ProblemSetQuerySet.as_manager()

    class Meta:
        ordering = ["start_date", "end_date"]

    def __str__(self):
        return self.name

    def get_rule_engine(self) -> RuleEngine:
        class_ = get_rule_engine_class(self.rule_engine)
        return class_(self)

    @property
    def end_date_time(self):
        return datetime.combine(self.end_date, time(hour=23, minute=59, second=59))


class ProblemText(TypedDict):
    text: str
    is_visible: bool


class Problem(models.Model):
    id: int
    name = models.CharField(blank=True, max_length=256)
    number = models.IntegerField(default=0)
    problem_set = models.ForeignKey(
        ProblemSet, on_delete=models.CASCADE, related_name="problems"
    )
    problem_set_id: int

    file_points = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    judge_points = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    text_points = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    judge_namespace = models.CharField(max_length=256, blank=True)
    judge_task = models.CharField(max_length=256, blank=True)

    text_answer = models.CharField(blank=True, max_length=256)

    text_set: "RelatedManager[Text]"

    class Meta:
        ordering = ["problem_set", "number"]

    def __str__(self):
        return f"{self.number}. {self.name}"

    def get_absolute_url(self):
        return reverse(
            "problem_detail",
            kwargs={"problem_set_id": self.problem_set_id, "number": self.number},
        )

    @property
    def accepted_submit_types(self) -> list[BaseSubmit.SubmitType]:
        types = []

        type_mapping = [
            ("file_points", BaseSubmit.SubmitType.FILE),
            ("judge_points", BaseSubmit.SubmitType.JUDGE),
            ("text_points", BaseSubmit.SubmitType.TEXT),
        ]

        for points, type_ in type_mapping:
            if getattr(self, points) > 0:
                types.append(type_)

        return types

    def get_all_texts(self) -> "dict[Text.Type, ProblemText]":
        texts = self.text_set.all()
        visible = self.get_visible_texts()

        output = {}
        for text in texts:
            output[text.type] = {
                "text": text.text,
                "is_visible": text.type in visible,
            }

        return output

    def get_visible_texts(self) -> "set[Text.Type]":
        return self.problem_set.get_rule_engine().get_visible_texts(self)


class Text(models.Model):
    class Type(models.TextChoices):
        PROBLEM_STATEMENT = "PS", "Problem statement"
        EXAMPLE_SOLUTION = "ES", "Example solution"
        SUSI_SMALL_HINT = "SSH", "Susi small hint"
        SUSI_LARGE_HINT = "SLH", "Susi large hint"

    text = models.TextField(blank=True)
    type = models.CharField(choices=Type.choices, max_length=3)
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="text_set"
    )

    class Meta:
        ordering = ["problem", "type"]
        constraints = [
            UniqueConstraint("problem", "type", name="text__unique_problem_type")
        ]

    def __str__(self):
        return f"{self.problem}({self.type})"
