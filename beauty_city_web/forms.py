from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
from django.contrib.auth.forms import AuthenticationForm
from .models import Appointment, PromoCode, Client


class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Логин"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Пароль"}
        )
    )


class AppointmentForm(forms.ModelForm):
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
        widgets = {
            "appointment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "min": timezone.now().date().isoformat(),
                }
            ),
            "appointment_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "step": "1800",
                    "min": "10:00",
                    "max": "19:00",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.appointment_time:
            self.initial["appointment_time"] = self.instance.appointment_time.strftime(
                "%H:%M"
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
        """Валидация времени: 10:00-19:00 с шагом 30 минут"""
        appointment_time = self.cleaned_data.get("appointment_time")

        if appointment_time:
            if isinstance(appointment_time, str):
                try:
                    hour, minute = map(int, appointment_time.split(":"))
                    appointment_time = datetime.time(hour, minute)
                except (ValueError, TypeError):
                    raise ValidationError("Неверный формат времени")

            hour = appointment_time.hour
            minute = appointment_time.minute

            if hour < 10 or hour > 19:
                raise ValidationError("Время должно быть с 10:00 до 19:00")

            if minute not in [0, 30]:
                raise ValidationError(
                    "Время должно быть с шагом 30 минут (например: 10:00, 10:30, 11:00)"
                )

        return appointment_time

    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if appointment_date and appointment_time:
            now = timezone.now()

            if isinstance(appointment_time, str):
                try:
                    hour, minute = map(int, appointment_time.split(":"))
                    appointment_time = datetime.time(hour, minute)
                except (ValueError, TypeError):
                    return cleaned_data

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
                        f"При записи на сегодня минимальное время: {min_datetime.strftime('%H:%M')}"
                    )

        return cleaned_data


class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = [
            "code",
            "discount_type",
            "discount_value",
            "description",
            "valid_from",
            "valid_to",
            "is_active",
            "max_uses",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "valid_to": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")

        if valid_from and valid_to and valid_from >= valid_to:
            raise ValidationError("Дата окончания должна быть позже даты начала")

        return cleaned_data


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["phone", "name", "email"]
