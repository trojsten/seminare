from typing import Callable, Protocol

from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from seminare.contests.models import Contest
from seminare.problems.models import ProblemSet
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
        site = get_current_site(self.request)
        return get_object_or_404(Contest, site=site, id=self.kwargs["contest_id"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contest"] = self.contest
        return ctx


class WithProblemSet(MixinProtocol):
    @cached_property
    def problem_set(self) -> ProblemSet:
        # site = get_current_site(self.request)
        return get_object_or_404(ProblemSet, id=self.kwargs["problem_set_id"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem_set"] = self.problem_set
        return ctx


class WithProblem(MixinProtocol):
    @cached_property
    def problem(self) -> ProblemSet:
        # site = get_current_site(self.request)
        return get_object_or_404(ProblemSet, id=self.kwargs["problem_id"])

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
