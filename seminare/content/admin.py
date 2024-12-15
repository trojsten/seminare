from django.contrib import admin

from seminare.content.models import MenuGroup, MenuItem, Page, Post


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_filter = ["site"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass


@admin.register(MenuGroup)
class MenuGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    pass
