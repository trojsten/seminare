# Create your views here.
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.views.generic import ListView

from seminare.users.mixins.permissions import ContestOrganizerRequired
from seminare.users.models import User


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
