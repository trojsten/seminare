from django.core.exceptions import ImproperlyConfigured
from django.views.generic import DeleteView, FormView, ListView

from seminare.organizer.views import WithBreadcrumbs
from seminare.style.tables import Table


class GenericTableView(WithBreadcrumbs, ListView):
    template_name = "org/generic/table.html"

    table_title = ""
    table_class: type[Table] | None = None
    table_links: list[tuple] = []

    def get_table_title(self):
        return self.table_title

    def get_table_links(self):
        return self.table_links

    def get_table_context(self):
        return {}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if not self.table_class:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing table_class."
            )

        ctx["table"] = self.table_class()
        ctx["table_title"] = self.get_table_title()
        ctx["table_links"] = self.get_table_links()
        ctx["table_context"] = self.get_table_context()
        return ctx


class GenericFormView(WithBreadcrumbs, FormView):
    template_name = "org/generic/form.html"

    form_title = ""
    form_description = ""
    form_multipart = False
    form_submit_label = "Uložiť"
    form_header_template = None
    form_links = []

    def get_form_title(self):
        return self.form_title

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = self.get_form_title()
        ctx["form_description"] = self.form_description
        ctx["form_multipart"] = self.form_multipart
        ctx["form_submit_label"] = self.form_submit_label
        ctx["form_header_template"] = self.form_header_template
        ctx["form_links"] = self.get_form_links()
        return ctx

    def get_form_links(self):
        return self.form_links


class GenericDeleteView(GenericFormView, DeleteView):
    template_name = "org/generic/delete.html"
    form_title = "Naozaj?"
    form_submit_label = "Vymazať"


class GenericFormTableView(WithBreadcrumbs, FormView, ListView):
    template_name = "org/generic/form_table.html"
    form_multipart = False
    form_submit_label = "Uložiť"
    form_table_title = ""
    form_table_links: list[tuple] = []
    table_class: type[Table] | None = None

    def get_form_table_title(self):
        return self.form_table_title

    def get_form_table_links(self):
        return self.form_table_links

    def get_form_table_context(self):
        return {}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_multipart"] = self.form_multipart
        ctx["form_submit_label"] = self.form_submit_label
        if not self.table_class:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing table_class."
            )

        ctx["table"] = self.table_class()
        ctx["form_table_title"] = self.get_form_table_title()
        ctx["form_table_links"] = self.get_form_table_links()
        ctx["form_table_context"] = self.get_form_table_context()
        return ctx
