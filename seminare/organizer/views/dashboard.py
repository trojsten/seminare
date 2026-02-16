from django.views.generic import TemplateView

from seminare.organizer.views import WithContest
from seminare.users.mixins.permissions import ContestOrganizerRequired


class ContestDashboardView(ContestOrganizerRequired, WithContest, TemplateView):
    template_name = "org/contest_dashboard.html"
