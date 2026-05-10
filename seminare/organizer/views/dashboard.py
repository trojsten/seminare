from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView

from seminare.organizer.views import WithContest
from seminare.users.mixins.permissions import ContestOrganizerRequired


class ContestDashboardView(ContestOrganizerRequired, WithContest, TemplateView):
    template_name = "org/contest_dashboard.html"


class AdminRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_staff:
            return reverse("admin:index")
        return reverse("org:contest_dashboard")
