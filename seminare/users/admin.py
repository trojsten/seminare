from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdmin(DjangoUserAdmin):
    def get_fieldsets(self, request, obj=...):
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets + (
            (
                _("Supplemental info"),
                {"fields": ("category",)},
            ),
        )


admin.site.register(User, UserAdmin)
