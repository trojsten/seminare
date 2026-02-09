from django.urls import path

from seminare.users.views import UserAutocompleteView

urlpatterns = [
    path(
        "autocomplete/user/", UserAutocompleteView.as_view(), name="user_autocomplete"
    ),
]
