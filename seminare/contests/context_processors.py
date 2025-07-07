from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest

from seminare.contests.models import Contest


def contest(request: HttpRequest) -> dict:
    site = get_current_site(request)

    contest = Contest.objects.get(site=site)

    return {"contest": contest}
