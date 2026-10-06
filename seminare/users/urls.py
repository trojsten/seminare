from django.urls import path

from seminare.users.views import (
    DebugNotificationView,
    NotificationDeleteAllView,
    NotificationMarkAllReadView,
    NotificationSeenView,
    NotificationSettingsView,
    PushSubscribeView,
    PushUnsubscribeView,
    PushVapidView,
    ServiceWorkerView,
    UserAutocompleteView,
)

urlpatterns = [
    path("sw.js", ServiceWorkerView.as_view(), name="service_worker"),
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
        "upozornenia/test/",
        DebugNotificationView.as_view(),
        name="notification_debug",
    ),
    path(
        "upozornenia/<int:notification_id>/",
        NotificationSeenView.as_view(),
        name="notification_seen",
    ),
    path("upozornenia/push/vapid/", PushVapidView.as_view(), name="push_vapid"),
    path(
        "upozornenia/push/subscribe/",
        PushSubscribeView.as_view(),
        name="push_subscribe",
    ),
    path(
        "upozornenia/push/unsubscribe/",
        PushUnsubscribeView.as_view(),
        name="push_unsubscribe",
    ),
]
