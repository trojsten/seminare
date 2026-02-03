from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
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


class OIDCAuthentication(BaseAuthentication):
    def authenticate(self, request):
        client_id = request.headers.get("X-Client-ID")
        client_secret = request.headers.get("X-Client-Secret")

        if not client_id or not client_secret:
            raise AuthenticationFailed("Missing authentication headers")

        if client_id != settings.OIDC_RP_CLIENT_ID or not check_password(
            settings.OIDC_RP_CLIENT_SECRET, client_secret
        ):
            raise AuthenticationFailed()

        return (None, None)
