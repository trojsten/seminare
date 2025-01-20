from typing import Callable, Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpRequest, HttpResponseRedirect

from seminare.users.logic.permissions import has_contest_role
from seminare.users.models import ContestRole, User


class MixinProtocol(Protocol):
    request: HttpRequest
    dispatch: Callable


class AccessMixin(MixinProtocol):
    def check_access(self) -> bool:
        raise ImproperlyConfigured(
            f"{self.__class__.__name__} does not override check_access method."
        )

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(settings.LOGIN_URL)

        if not self.check_access():
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)


class ContestAccessMixin(AccessMixin):
    required_role = None

    def get_permission_contest(self):
        raise ImproperlyConfigured(
            f"{self.__class__.__name__} does not provide permission contest."
        )

    def get_required_role(self):
        if self.required_role is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not have required_role or get_required_role."
            )

        return self.required_role

    def check_access(self) -> bool:
        assert isinstance(self.request.user, User)
        return has_contest_role(
            self.request.user, self.get_permission_contest(), self.get_required_role()
        )


class ContestAdminRequired(ContestAccessMixin):
    required_role = ContestRole.Role.ADMINISTRATOR


class ContestOrganizerRequired(ContestAccessMixin):
    required_role = ContestRole.Role.ORGANIZER
