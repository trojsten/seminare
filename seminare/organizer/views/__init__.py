from typing import Protocol

from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from seminare.contests.models import Contest


class ViewLike(Protocol):
    request: HttpRequest
    kwargs: dict

    def get_context_data(self, **kwargs) -> dict: ...


class WithContestProtocol(ViewLike, Protocol):
    contest: Contest


class WithContest:
    @cached_property
    def contest(self: WithContestProtocol) -> Contest:
        site = get_current_site(self.request)
        return get_object_or_404(Contest, site=site, id=self.kwargs["contest_id"])

    def get_context_data(self: WithContestProtocol, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contest"] = self.contest
        return ctx
