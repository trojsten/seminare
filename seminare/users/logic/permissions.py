from collections import defaultdict

from django.core.exceptions import SuspiciousOperation

from seminare.contests.models import Contest
from seminare.users.models import ContestRole, User


def get_contest_role(user: User, contest: Contest) -> ContestRole | None:
    """
    Returns the ContestRole for `user` and `contest` or None if user does not have any role in the selected contest.

    ContestRole values are cached for subsequent calls.
    """
    if hasattr(user, "_contest_role_cache"):
        role_cache = getattr(user, "_contest_role_cache")
        if contest.id in role_cache:
            return role_cache[contest.id]
    else:
        role_cache = {}

    role = ContestRole.objects.filter(user=user, contest=contest).first()
    role_cache[contest.id] = role
    setattr(user, "_contest_role_cache", role_cache)
    return role


def get_contest_role_for_users(
    users: list[User], contest: Contest
) -> dict[User, ContestRole | None]:
    """
    Returns a dictionary mapping each user in `users` to their ContestRole (or None) for `contest`.
    """
    out: dict[User, ContestRole | None] = defaultdict(lambda: None)
    roles = ContestRole.objects.filter(user__in=users, contest=contest)

    for role in roles:
        out[role.user] = role

    return out


def preload_contest_roles(users: list[User], contest: Contest) -> None:
    """
    Preloads contest roles for a list of users in a specific contest.
    This is useful to avoid multiple database queries when checking roles later.
    """
    roles = get_contest_role_for_users(users, contest)

    for user in users:
        setattr(
            user,
            "_contest_role_cache",
            {contest.id: roles[user]},
        )


def has_contest_role(user: User, contest: Contest, role: ContestRole.Role) -> bool:
    """
    Checks whether `user` has at least `role` in `contest`.

    Passing an unauthenticated user will result in a SuspiciousOperation.
    """
    if not user.is_authenticated:
        raise SuspiciousOperation("has_contest_role() got an AnonymousUser")

    if user.is_superuser:
        return True

    user_role = get_contest_role(user, contest)
    if not user_role:
        return False

    return user_role.role >= role


def is_contest_administrator(user: User, contest: Contest) -> bool:
    """
    Checks whether `user` is an administrator of `contest`.
    """
    return has_contest_role(user, contest, ContestRole.Role.ADMINISTRATOR)


def is_contest_organizer(user: User, contest: Contest) -> bool:
    """
    Checks whether `user` is an organizer or administrator of `contest`.
    """
    return has_contest_role(user, contest, ContestRole.Role.ORGANIZER)
