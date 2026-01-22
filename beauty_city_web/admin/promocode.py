from django.contrib import admin


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "description",
        "discount_type",
        "discount_value",
        "valid_from",
        "valid_to",
        "is_active",
    )
    list_filter = ("is_active", "discount_type")
    search_fields = ("code", "description")
    list_editable = ("is_active",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("appointments")
