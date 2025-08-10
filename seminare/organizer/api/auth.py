from typing import TYPE_CHECKING

from rest_framework.permissions import BasePermission

from seminare.contests.utils import get_current_contest
from seminare.users.logic.permissions import is_contest_administrator
from seminare.users.models import User

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class IsContestAdmin(BasePermission):
    def has_permission(self, request: "Request", view: "APIView") -> bool:
        if not request.user.is_authenticated:
            return False

        assert isinstance(request.user, User)
        contest = get_current_contest(request)
        return is_contest_administrator(request.user, contest)
