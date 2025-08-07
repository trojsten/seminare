from django.http import HttpRequest

from seminare.contests.utils import get_current_contest


def contest(request: HttpRequest) -> dict:
    return {"contest": get_current_contest(request)}
