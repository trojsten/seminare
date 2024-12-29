from typing import Any

from django.template.loader import render_to_string


class Table:
    fields: list[str] = []
    templates: dict[str, str] = {}
    labels: dict[str, str] = {}

    def get_links(
        self, object: Any, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        return []

    def render_field(self, field: str, object: Any, context: dict):
        if field in self.templates:
            template = self.templates[field]
            value = getattr(object, field, None)
            context.update({"object": object, "field": field, "value": value})
            return render_to_string(template, context)

        if hasattr(self, f"get_{field}_content"):
            fn = getattr(self, f"get_{field}_content")
            return fn(object)

        return getattr(object, field, "")
