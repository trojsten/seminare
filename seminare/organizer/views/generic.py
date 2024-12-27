from django.core.exceptions import ImproperlyConfigured
from django.views.generic import ListView

from seminare.style.tables import Table


class GenericTableView(ListView):
    template_name = "org/generic/table.html"

    table_title = ""
    table_class: type[Table] | None = None
    table_links: list[tuple[str, str, str] | tuple[str, str, str, str]] = []

    def get_table_title(self):
        return self.table_title

    def get_table_links(self):
        return self.table_links

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if not self.table_class:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing table_class."
            )

        ctx["table"] = self.table_class()
        ctx["table_title"] = self.get_table_title()
        ctx["table_links"] = self.get_table_links()
        return ctx
