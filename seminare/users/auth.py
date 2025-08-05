from datetime import date

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from seminare.users.logic.schools import get_grade_from_type_year
from seminare.users.models import School, User


def logout_url(request):
    return "https://id.trojsten.sk/oauth/logout"


class TrojstenOIDCAB(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        email = claims.get("email")
        id = claims.get("sub")
        if not email and not id:
            return User.objects.none()
        return User.objects.filter(trojsten_id=id)

    def create_user(self, claims):
        user = User()
        self._set_user(user, claims)
        user.save()

        return user

    def update_user(self, user, claims):
        self._set_user(user, claims)
        user.save()

        return user

    def _set_user(self, user, claims):
        user.trojsten_id = claims.get("sub")
        user.email = claims.get("email")
        user.username = claims.get("preferred_username")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")

        self._update_school_info(user, claims.get("school_info"))

    def _update_school_info(self, user, school_info):
        if not school_info:
            user.current_school = None
            user.current_grade = ""
            return

        end_date = school_info["end_date"]
        is_expired = end_date and date.fromisoformat(end_date) < date.today()
        if is_expired:
            user.current_school = None
            user.current_grade = ""
            return

        school_data = school_info["school"]
        school, _ = School.objects.get_or_create(
            edu_id=school_data["eduid"],
            defaults={
                "name": school_data["name"],
                "address": school_data["address"],
            },
        )
        user.current_school = school

        school_type = school_info["school_type"]
        current_year = int(school_info["current_year"])
        user.current_grade = get_grade_from_type_year(school_type, current_year) or ""
