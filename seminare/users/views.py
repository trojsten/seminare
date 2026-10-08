import json
from functools import cached_property

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import (
    FileResponse,
    Http404,
    HttpRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, View
from django.views.generic.edit import FormView

from seminare.contests.utils import get_current_contest
from seminare.users.forms import NotificationPreferencesForm, channel_field_name
from seminare.users.logic.notifications import (
    CONFIGURABLE_TYPES,
    schedule_debug_notification,
)
from seminare.users.logic.push import get_vapid_keys
from seminare.users.mixins.permissions import ContestOrganizerRequired
from seminare.users.models import (
    Notification,
    NotificationChannel,
    NotificationPreferences,
    PushSubscription,
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

        context["show_debug_notification"] = settings.DEBUG
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


class DebugNotificationView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:
        if not settings.DEBUG:
            raise Http404

        schedule_debug_notification(request.user.id, get_current_contest(request).id)
        messages.success(request, "Testovacie upozornenie príde o minútu.")
        return redirect_back(request, reverse("homepage"))


class ServiceWorkerView(View):
    def get(self, request: HttpRequest) -> FileResponse:
        path = finders.find("push/sw.js")
        if not path:
            raise Http404

        response = FileResponse(open(path, "rb"), content_type="application/javascript")
        response["Cache-Control"] = "no-cache"
        response["Service-Worker-Allowed"] = "/"
        return response


def _parse_push_subscription(request: HttpRequest) -> tuple[str, str, str] | None:
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data["keys"]
        p256dh = keys["p256dh"]
        auth = keys["auth"]
    except json.JSONDecodeError, KeyError, TypeError:
        return None

    if (
        not isinstance(endpoint, str)
        or not endpoint.startswith("https://")
        or not isinstance(p256dh, str)
        or not isinstance(auth, str)
        or len(p256dh) > 255
        or len(auth) > 255
    ):
        return None

    return endpoint, p256dh, auth


class PushVapidView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        public_key, private_key = get_vapid_keys()
        if not public_key or not private_key:
            return JsonResponse({"error": "not_configured"}, status=503)

        return JsonResponse({"publicKey": public_key})


class PushSubscribeView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> JsonResponse:
        parsed = _parse_push_subscription(request)
        if parsed is None:
            return JsonResponse({"error": "invalid"}, status=400)

        endpoint, p256dh, auth = parsed
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={"user": request.user, "p256dh": p256dh, "auth": auth},
        )
        return JsonResponse({"ok": True})


class PushUnsubscribeView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data = json.loads(request.body)
            endpoint = data["endpoint"]
        except json.JSONDecodeError, KeyError, TypeError:
            return JsonResponse({"error": "invalid"}, status=400)

        if not isinstance(endpoint, str):
            return JsonResponse({"error": "invalid"}, status=400)

        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return JsonResponse({"ok": True})
