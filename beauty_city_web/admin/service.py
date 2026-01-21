from django.contrib import admin


class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)
    ordering = ("order",)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "duration", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "category__name")
    list_editable = ("is_active", "price")
    ordering = ("category", "order")
