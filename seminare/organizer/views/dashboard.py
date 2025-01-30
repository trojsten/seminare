from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from seminare.contests.models import Contest
from seminare.organizer.views import WithContest


class ContestSwitchView(TemplateView):
    # TODO: Permission check

    template_name = "org/contest_switch.html"

    @cached_property
    def contests(self):
        site = get_current_site(self.request)
        return Contest.objects.filter(site=site).all()

    def get(self, *args, **kwargs):
        if len(self.contests) == 1:
            return HttpResponseRedirect(
                reverse("org:contest_dashboard", args=[self.contests[0].id])
            )

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contests"] = self.contests
        return ctx


class ContestDashboardView(WithContest, TemplateView):
    template_name = "org/contest_dashboard.html"
