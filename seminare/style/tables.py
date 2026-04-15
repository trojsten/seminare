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

    def get_attr(self, value: Any, field: str) -> Any:
        for part in field.split("__"):
            value = getattr(value, part, None)
            if value is None:
                break
        return value

    def render_field(self, field: str, object: Any, context: dict):
        if field in self.templates:
            template = self.templates[field]
            value = self.get_attr(object, field)
            context.update({"object": object, "field": field, "value": value})
            return render_to_string(template, context)

        if hasattr(self, f"get_{field}_content"):
            fn = getattr(self, f"get_{field}_content")
            return fn(object)

        return self.get_attr(object, field)
