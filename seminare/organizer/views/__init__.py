from typing import Callable, Protocol

from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from seminare.contests.models import Contest
from seminare.submits.models import BaseSubmit


class MixinProtocol(Protocol):
    request: HttpRequest
    kwargs: dict
    get_context_data: Callable[..., dict]


class WithContest(MixinProtocol):
    @cached_property
    def contest(self) -> Contest:
        site = get_current_site(self.request)
        return get_object_or_404(Contest, site=site, id=self.kwargs["contest_id"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contest"] = self.contest
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
