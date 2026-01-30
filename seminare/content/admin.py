from django.contrib import admin

from seminare.content.models import MenuGroup, MenuItem, Page, Post


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "contest"]
    list_filter = ["contest"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "author"]


@admin.register(MenuGroup)
class MenuGroupAdmin(admin.ModelAdmin):
    list_display = ["title", "contest", "order"]
    list_filter = ["contest"]
    list_editable = ["order"]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["title", "group", "order"]
    list_filter = ["group__contest", "group"]
    list_editable = ["order"]
