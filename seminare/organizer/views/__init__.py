from typing import Callable, Protocol

from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from seminare.content.models import MenuGroup, MenuItem
from seminare.contests.models import Contest
from seminare.contests.utils import get_current_contest
from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import BaseSubmit


class MixinProtocol(Protocol):
    request: HttpRequest
    kwargs: dict
    get_context_data: Callable[..., dict]


class WithBreadcrumbs(MixinProtocol):
    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = self.get_breadcrumbs()
        return ctx


class WithContest(MixinProtocol):
    @cached_property
    def contest(self) -> Contest:
        return get_current_contest(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contest"] = self.contest
        return ctx


class WithProblemSet(WithContest, MixinProtocol):
    @cached_property
    def problem_set(self) -> ProblemSet:
        return get_object_or_404(
            ProblemSet, slug=self.kwargs["problem_set_slug"], contest=self.contest
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem_set"] = self.problem_set
        return ctx


class WithProblem(WithProblemSet, MixinProtocol):
    @cached_property
    def problem(self) -> Problem:
        return get_object_or_404(
            Problem, problem_set=self.problem_set, number=self.kwargs["number"]
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem"] = self.problem
        return ctx


class WithSubmit(MixinProtocol):
    @cached_property
    def submit(self) -> BaseSubmit:
        filter = {}
        if hasattr(self, "contest"):
            filter["problem__problem_set__contest"] = self.contest  # pyright: ignore
        submit = BaseSubmit.get_submit_by_id(self.kwargs["submit_id"], **filter)
        if not submit:
            raise Http404()
        return submit

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["submit"] = self.submit
        return ctx


class WithMenuGroup(WithContest, MixinProtocol):
    @cached_property
    def menu_group(self) -> MenuGroup:
        return get_object_or_404(
            MenuGroup, id=self.kwargs["pk"], contest=get_current_contest(self.request)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["menu_group"] = self.menu_group
        return ctx


class WithMenuItem(WithMenuGroup, MixinProtocol):
    @cached_property
    def menu_item(self) -> MenuItem:
        return get_object_or_404(
            MenuItem, id=self.kwargs["item_pk"], group=self.menu_group
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["menu_item"] = self.menu_item
        return ctx
