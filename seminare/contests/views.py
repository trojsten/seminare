from django.views.generic import TemplateView

from seminare.contests.utils import get_current_contest


class HomepageView(TemplateView):
    def get_template_names(self) -> list[str]:
        contest = get_current_contest(self.request)
        return [
            f"homepage.{contest.short_name.lower()}.html",
            "homepage.html",
        ]
