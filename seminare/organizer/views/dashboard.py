from django.views.generic import TemplateView

from seminare.organizer.views import WithContest


class ContestDashboardView(WithContest, TemplateView):
    template_name = "org/contest_dashboard.html"
