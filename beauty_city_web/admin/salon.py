from django.contrib import admin

class SalonAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address", "phone")
    list_editable = ("is_active",)
