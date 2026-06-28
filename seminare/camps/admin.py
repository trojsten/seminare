from django.contrib import admin

from seminare.camps.models import Camp, CampAttendee


class CampAttendeeInline(admin.TabularInline):
    model = CampAttendee
    extra = 2


@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "start_date", "end_date", "is_finalized"]
    inlines = [CampAttendeeInline]
