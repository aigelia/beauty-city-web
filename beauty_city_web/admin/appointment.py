from django.contrib import admin
from ..forms.appointment import AppointmentAdminForm


class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentAdminForm

    list_display = (
        "id",
        "client",
        "master",
        "service",
        "appointment_date",
        "appointment_time",
        "status",
        "final_price",
        "has_promo",
    )
    list_filter = ("status", "appointment_date", "salon", "master")
    search_fields = ("client__name", "client__phone", "master__name", "service__name")
    list_editable = ("status",)
    date_hierarchy = "appointment_date"

    ordering = ("-id",)

    readonly_fields = ("original_price", "discount_amount", "final_price", "created_at")

    fieldsets = (
        (None, {"fields": ("client", "master", "service", "salon")}),
        (
            "Дата и время",
            {"fields": ("appointment_date", "appointment_time", "status")},
        ),
        (
            "Цены",
            {
                "fields": ("original_price", "discount_amount", "final_price"),
                "classes": ("collapse", "wide"),
                "description": "Цены рассчитываются автоматически на основе услуги и промокода",
            },
        ),
        ("Дополнительно", {"fields": ("promo_code", "notes", "created_at")}),
    )

    def save_model(self, request, obj, form, change):
        """Сохраняем модель с автоматическим расчетом цен"""

        if obj.service:
            obj.original_price = obj.service.price

        if obj.promo_code and obj.promo_code.is_valid():
            obj.discount_amount = obj.promo_code.calculate_discount(obj.original_price)

            if not change:
                obj.promo_code.used_count += 1
                obj.promo_code.save()
        else:
            obj.discount_amount = 0

        obj.final_price = obj.original_price - obj.discount_amount

        super().save_model(request, obj, form, change)

    def has_promo(self, obj):
        return obj.promo_code is not None

    has_promo.boolean = True
    has_promo.short_description = "Промокод"
