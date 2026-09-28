from django import forms

from seminare.contests.models import Contest
from seminare.users.models import (
    NotificationChannel,
    NotificationPreferences,
    NotificationType,
    User,
)

CONFIGURABLE_TYPES = [
    NotificationType.PROBLEM_SET,
    NotificationType.SUBMIT_GRADED,
    NotificationType.POST,
]

DEFAULT_CHANNELS = [NotificationChannel.SITE]


def channel_field_name(type: NotificationType, channel: NotificationChannel) -> str:
    return f"{type.name.lower()}_{channel.name.lower()}"


class NotificationPreferencesForm(forms.Form):
    def __init__(
        self, *args, preferences: dict[int, list[int]] | None = None, **kwargs
    ):
        super().__init__(*args, **kwargs)

        preferences = preferences or {}

        for notification_type in CONFIGURABLE_TYPES:
            enabled = preferences.get(
                notification_type.value, [channel.value for channel in DEFAULT_CHANNELS]
            )
            for channel in NotificationChannel:
                self.fields[channel_field_name(notification_type, channel)] = (
                    forms.BooleanField(
                        required=False,
                        label=channel.label,
                        initial=channel.value in enabled,
                        widget=forms.CheckboxInput(attrs={"class": "checkbox"}),
                    )
                )

    def save(self, user: User, contest: Contest) -> None:
        for notification_type in CONFIGURABLE_TYPES:
            channels = [
                channel.value
                for channel in NotificationChannel
                if self.cleaned_data[channel_field_name(notification_type, channel)]
            ]
            NotificationPreferences.objects.update_or_create(
                user=user,
                contest=contest,
                type=notification_type.value,
                defaults={"channels": channels},
            )
