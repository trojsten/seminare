from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from seminare.contests.models import Contest


class WithContest:
    @cached_property
    def contest(self) -> Contest:
        site = get_current_site(self.request)
        return get_object_or_404(Contest, site=site, id=self.kwargs["contest_id"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contest"] = self.contest
        return ctx
