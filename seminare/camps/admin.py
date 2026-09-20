from django.contrib import admin

from seminare.camps.models import Camp, CampAttendee


class CampAttendeeInline(admin.TabularInline):
    model = CampAttendee
    autocomplete_fields = ["user"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "camp")


@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "start_date", "end_date", "is_finalized"]
    inlines = [CampAttendeeInline]
