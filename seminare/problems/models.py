from pathlib import PurePath
from typing import TYPE_CHECKING, Self, Type, TypedDict

from django.core.files.storage import storages
from django.db import models
from django.db.models import UniqueConstraint
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

from seminare.rules import RuleEngine, get_rule_engine_class
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from seminare.users.models import Enrollment


class ProblemSetQuerySet(models.QuerySet):
    def for_user(self, user):
        # TODO: real permission check
        return self.filter(is_public=True)

    def only_current(self):
        return self.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())


def get_statement_filename(instance: "ProblemSet", filename: str) -> str:
    return str(PurePath(instance.contest.data_root) / instance.slug / "zadania.pdf")


def get_solution_filename(instance: "ProblemSet", filename: str) -> str:
    return str(PurePath(instance.contest.data_root) / instance.slug / "vzoraky.pdf")


class ProblemSet(models.Model):
    id: int
    slug = models.SlugField(max_length=64)

    contest = models.ForeignKey("contests.Contest", on_delete=models.CASCADE)
    contest_id: int

    name = models.CharField(max_length=256)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    is_public = models.BooleanField(default=False)

    rule_engine = models.CharField(max_length=512)
    rule_engine_options = models.JSONField(default=dict, blank=True)

    is_finalized = models.BooleanField(default=False)

    statement_pdf = models.FileField(
        upload_to=get_statement_filename,
        storage=storages["private"],
        blank=True,
        null=True,
    )
    solution_pdf = models.FileField(
        upload_to=get_solution_filename,
        storage=storages["private"],
        blank=True,
        null=True,
    )

    objects = ProblemSetQuerySet.as_manager()
    enrollment_set: "RelatedManager[Enrollment]"
    problems: "RelatedManager[Problem]"

    class Meta:
        ordering = ["start_date", "end_date"]
        constraints = [
            UniqueConstraint("contest", "slug", name="problemset__contest_slug__unique")
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self._is_finalized and self.is_finalized:
            self.is_finalized = False
            self.get_rule_engine().close_problemset()
            self.is_finalized = True

        return super().save(*args, **kwargs)

    _is_finalized: bool = False

    @classmethod
    def from_db(cls, *args, **kwargs) -> Self:
        instance = super().from_db(*args, **kwargs)

        instance._is_finalized = instance.is_finalized

        return instance

    def get_rule_engine(self) -> RuleEngine:
        class_ = get_rule_engine_class(self.rule_engine)
        return class_(self)

    @property
    def is_running(self) -> bool:
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def set_frozen_results(self, table: str, data: dict):
        return ProblemSetFrozenResults.objects.update_or_create(
            problem_set=self, table=table, defaults={"data": data}
        )

    def get_frozen_results(self, table: str) -> dict:
        return get_object_or_404(
            ProblemSetFrozenResults, problem_set=self, table=table
        ).data


class ProblemSetFrozenResults(models.Model):
    id: int

    problem_set = models.ForeignKey(ProblemSet, on_delete=models.CASCADE)
    table = models.CharField(max_length=64)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("problem_set", "table")

    def __str__(self):
        return f"{self.problem_set} - {self.table}"


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
        constraints = [
            UniqueConstraint(
                "problem_set", "number", name="problem__problem_set_number__unique"
            ),
        ]
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

    @property
    def accepted_submit_classes(self) -> list[Type[BaseSubmit]]:
        types = []

        type_mapping = [
            ("file_points", FileSubmit),
            ("judge_points", JudgeSubmit),
            ("text_points", TextSubmit),
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

    def get_data_root(self, absolute=False) -> str:
        path = PurePath("rounds") / self.problem_set.slug / str(self.number)
        if absolute:
            return str(self.problem_set.contest.data_root / path)
        return str(path)

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
