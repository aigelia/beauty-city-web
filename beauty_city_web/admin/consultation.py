from django.contrib import admin
from ..forms.consultation import ConsultationAdminForm


class ConsultationAdmin(admin.ModelAdmin):
    form = ConsultationAdminForm

    list_display = (
        "client",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("client__name", "client__phone", "created_at")
    list_editable = ("status",)
    ordering = ("created_at",)
    readonly_fields = ("created_at",)
