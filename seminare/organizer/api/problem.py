from typing import Any
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError

from seminare.contests.utils import get_current_contest
from seminare.problems.models import Problem, ProblemSet, Text


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:  # pyright:ignore
        model = Problem
        exclude = ["id", "problem_set"]

    def validate(self, attrs):
        problem_set = self.context["problem_set"]
        if self.instance:
            assert isinstance(self.instance, Problem)
            self.instance.problem_set = problem_set
            self.instance.full_clean()
        else:
            Problem(**attrs, problem_set=problem_set).full_clean()
        return attrs


class ProblemViewSet(viewsets.ModelViewSet):
    serializer_class = ProblemSerializer
    lookup_field = "number"

    def get_queryset(self):
        return Problem.objects.filter(problem_set=self.problem_set)

    @cached_property
    def problem_set(self):
        contest = get_current_contest(self.request)
        return get_object_or_404(
            ProblemSet,
            slug=self.kwargs.get("problemset"),
            contest=contest,
        )

    def perform_create(self, serializer):
        serializer.save(problem_set=self.problem_set)

    def perform_update(self, serializer):
        serializer.save(problem_set=self.problem_set)

    def get_serializer_context(self) -> dict[str, Any]:
        ctx = super().get_serializer_context()
        ctx["problem_set"] = self.problem_set
        return ctx


class TextSerializer(serializers.ModelSerializer):
    class Meta:  # pyright:ignore
        model = Text
        exclude = ["id", "problem"]

    def validate(self, attrs):
        problem = self.context["problem"]
        if self.instance:
            assert isinstance(self.instance, Text)
            self.instance.problem = problem
            self.instance.full_clean()
        else:
            Text(**attrs, problem=problem).full_clean()
        return attrs


class TextViewSet(viewsets.ModelViewSet):
    serializer_class = TextSerializer
    lookup_field = "type"

    def get_queryset(self):
        return Text.objects.filter(problem=self.problem)

    @cached_property
    def problem(self):
        contest = get_current_contest(self.request)
        return get_object_or_404(
            Problem,
            problem_set__slug=self.kwargs.get("problemset"),
            number=self.kwargs.get("problem"),
            problem_set__contest=contest,
        )

    def perform_create(self, serializer):
        serializer.save(problem=self.problem)

    def perform_update(self, serializer):
        serializer.save(problem=self.problem)

    def get_serializer_context(self) -> dict[str, Any]:
        ctx = super().get_serializer_context()
        ctx["problem"] = self.problem
        return ctx
