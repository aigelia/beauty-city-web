from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

from .models import (
    Salon,
    ServiceCategory,
    Service,
    Master,
    Client,
    PromoCode,
    Appointment,
    Statistic,
    Review,
)


class SalonAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address", "phone")
    list_editable = ("is_active",)


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


class MasterAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty", "experience", "rating", "is_active")
    list_filter = ("is_active", "specialty")
    search_fields = ("name", "specialty")
    list_editable = ("is_active", "rating")
    filter_horizontal = ("salons", "services")
    ordering = ("order",)


class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "registration_date", "appointments_count")
    search_fields = ("name", "phone", "email")

    def appointments_count(self, obj):
        return obj.appointments.count()

    appointments_count.short_description = "Количество записей"


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "description",
        "discount_type",
        "discount_value",
        "valid_from",
        "valid_to",
        "is_active",
        "used_count",
        "max_uses",
    )
    list_filter = ("is_active", "discount_type")
    search_fields = ("code", "description")
    list_editable = ("is_active", "max_uses")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("appointments")



class AppointmentAdminForm(forms.ModelForm):
    appointment_time = forms.ChoiceField(
        choices=[],
        label="Время записи",
        help_text="Время с 10:00 до 19:00 с шагом 30 минут",
    )

    class Meta:
        model = Appointment
        fields = [
            "client",
            "master",
            "service",
            "salon",
            "appointment_date",
            "appointment_time",
            "status",
            "promo_code",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        time_choices = []
        for hour in range(10, 20):
            for minute in (0, 30):
                if hour == 19 and minute == 30:
                    break
                time_str = f"{hour:02d}:{minute:02d}"
                time_choices.append((time_str, time_str))

        self.fields["appointment_time"].choices = [("", "---------")] + time_choices

        if self.instance and self.instance.appointment_time:
            current_time = self.instance.appointment_time.strftime("%H:%M")
            self.initial["appointment_time"] = current_time

        today = timezone.now().date()
        self.fields["appointment_date"].widget = forms.DateInput(
            attrs={"type": "date", "min": today.isoformat()}
        )

    def clean_appointment_date(self):
        """Валидация даты - нельзя выбирать прошедшие дни"""
        appointment_date = self.cleaned_data.get("appointment_date")

        if appointment_date:
            today = timezone.now().date()
            if appointment_date < today:
                raise ValidationError("Нельзя выбрать прошедшую дату")

        return appointment_date

    def clean_appointment_time(self):
        """Преобразуем строку времени в объект time и валидируем"""
        time_str = self.cleaned_data.get("appointment_time")
        if not time_str:
            return None

        try:
            hour, minute = map(int, time_str.split(":"))
            appointment_time = datetime.time(hour, minute)

            if hour < 10 or hour > 19:
                raise ValidationError("Время должно быть с 10:00 до 19:00")

            if minute not in [0, 30]:
                raise ValidationError(
                    "Время должно быть с шагом 30 минут (например: 10:00, 10:30, 11:00)"
                )

            return appointment_time

        except (ValueError, TypeError):
            raise ValidationError("Неверный формат времени")

    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if appointment_date and appointment_time:
            now = timezone.now()

            selected_datetime = datetime.datetime.combine(
                appointment_date,
                appointment_time,
                tzinfo=timezone.get_current_timezone(),
            )

            if selected_datetime < now:
                raise ValidationError("Нельзя записаться на прошедшее время")

            if appointment_date == now.date():
                min_datetime = now + datetime.timedelta(hours=1)
                if selected_datetime < min_datetime:
                    raise ValidationError(
                        "При записи на сегодня минимальное время через 1 час"
                    )

        return cleaned_data


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


class StatisticAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "total_appointments",
        "completed_appointments",
        "total_revenue",
        "new_clients",
    )
    ordering = ("-date",)
    date_hierarchy = "date"


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "text",
        "rating",
    )
    ordering = ("-date",)
    date_hierarchy = "date"


# Регистрация моделей в админке
admin.site.register(Salon, SalonAdmin)
admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Master, MasterAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Statistic, StatisticAdmin)
admin.site.register(Review, ReviewAdmin)

# Настройка админ-панели
admin.site.site_header = "BeautyCity Администрация"
admin.site.site_title = "BeautyCity Админ"
admin.site.index_title = "Панель управления BeautyCity"
