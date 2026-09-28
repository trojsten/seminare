from django.urls import path

from seminare.users.views import (
    NotificationDeleteAllView,
    NotificationMarkAllReadView,
    NotificationSeenView,
    NotificationSettingsView,
    UserAutocompleteView,
)

urlpatterns = [
    path(
        "autocomplete/user/", UserAutocompleteView.as_view(), name="user_autocomplete"
    ),
    path(
        "upozornenia/", NotificationSettingsView.as_view(), name="notification_settings"
    ),
    path(
        "upozornenia/precitane/",
        NotificationMarkAllReadView.as_view(),
        name="notification_mark_all_read",
    ),
    path(
        "upozornenia/vymazat/",
        NotificationDeleteAllView.as_view(),
        name="notification_delete_all",
    ),
    path(
        "upozornenia/<int:notification_id>/",
        NotificationSeenView.as_view(),
        name="notification_seen",
    ),
]
