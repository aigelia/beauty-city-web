from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
from ..models import Appointment


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
