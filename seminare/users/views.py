from functools import cached_property

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, View
from django.views.generic.edit import FormView

from seminare.contests.utils import get_current_contest
from seminare.users.forms import (
    CONFIGURABLE_TYPES,
    NotificationPreferencesForm,
    channel_field_name,
)
from seminare.users.mixins.permissions import ContestOrganizerRequired
from seminare.users.models import (
    Notification,
    NotificationChannel,
    NotificationPreferences,
    User,
)
from seminare.utils import redirect_back


class UserAutocompleteView(ContestOrganizerRequired, ListView):
    template_name = "users/user_autocomplete.html"

    def get_queryset(self):
        qs = User.objects.all()

        query = self.request.GET.get("q")
        if query:
            qs = qs.annotate(
                full_name=Concat("first_name", Value(" "), "last_name")
            ).filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(full_name__icontains=query)
            )

        return qs[:10]


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:
        Notification.objects.filter(user=request.user, viewed_at__isnull=True).update(
            viewed_at=timezone.now()
        )

        return redirect_back(request, reverse("homepage"))


class NotificationDeleteAllView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:
        Notification.objects.filter(user=request.user).delete()

        return redirect_back(request, reverse("homepage"))


class NotificationSeenView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, notification_id: int) -> HttpResponseRedirect:
        notification = get_object_or_404(
            Notification, user=request.user, id=notification_id
        )

        if notification.viewed_at is None:
            notification.viewed_at = timezone.now()
            notification.save(update_fields=["viewed_at"])

        if notification.link:
            return HttpResponseRedirect(notification.link)

        return redirect_back(request, reverse("homepage"))


class NotificationSettingsView(LoginRequiredMixin, FormView):
    template_name = "users/notification_settings.html"
    form_class = NotificationPreferencesForm

    @cached_property
    def contest(self):
        return get_current_contest(self.request)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["preferences"] = {
            preference.type: preference.channels
            for preference in NotificationPreferences.objects.filter(
                user=self.request.user, contest=self.contest
            )
        }
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]

        context["rows"] = [
            {
                "label": notification_type.label,
                "channels": [
                    {
                        "label": channel.label,
                        "field": form[channel_field_name(notification_type, channel)],
                    }
                    for channel in NotificationChannel
                ],
            }
            for notification_type in CONFIGURABLE_TYPES
        ]

        return context

    def form_valid(self, form):
        form.save(user=self.request.user, contest=self.contest)
        messages.success(self.request, "Nastavenia upozornení boli uložené.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("notification_settings")
