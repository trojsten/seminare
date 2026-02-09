from django.forms import NumberInput
from django.urls import reverse_lazy

from seminare.users.models import User


class UserAutocompleteInput(NumberInput):
    input_type = "user"
    model = User
    template_name = "forms/autocomplete.html"
    autocomplete_url = reverse_lazy("user_autocomplete")

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        ctx["autocomplete_url"] = self.autocomplete_url
        if value:
            ctx["object"] = self.model.objects.filter(id=value).first()
        return ctx
