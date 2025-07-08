from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest

from seminare.contests.models import Contest


def get_current_contest(request: HttpRequest) -> Contest:
    if not hasattr(request, "_contest"):
        site = get_current_site(request)
        contest = Contest.objects.get(site=site)

        setattr(request, "_contest", contest)

    return getattr(request, "_contest")
