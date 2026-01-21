from django.contrib import admin


class MasterAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty", "experience", "rating", "is_active")
    list_filter = ("is_active", "specialty")
    search_fields = ("name", "specialty")
    list_editable = ("is_active", "rating")
    filter_horizontal = ("salons", "services")
    ordering = ("order",)
