from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import Appointment
from ..utils.validators import (
    validate_future_date,
    validate_working_hours,
    validate_appointment_datetime,
)


class BaseAppointmentForm(forms.ModelForm):
    """Базовый класс формы записи с общей валидацией"""

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

    def clean_appointment_date(self):
        """Валидация даты - нельзя выбирать прошедшие дни"""
        appointment_date = self.cleaned_data.get("appointment_date")
        validate_future_date(appointment_date)
        return appointment_date

    def clean_appointment_time(self):
        """Валидация времени"""
        time_value = self.cleaned_data.get("appointment_time")
        return validate_working_hours(time_value)

    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")
        master = cleaned_data.get("master")

        if appointment_date and appointment_time:
            validate_appointment_datetime(appointment_date, appointment_time)

            # Проверка на занятость времени у мастера
            if master:
                appointments = Appointment.objects.filter(
                    master=master,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    status__in=["pending", "confirmed"],
                )

                if self.instance and self.instance.pk:
                    appointments = appointments.exclude(pk=self.instance.pk)

                if appointments.exists():
                    raise ValidationError(
                        f"У мастера {master.name} уже есть запись на {appointment_date} в {appointment_time}"
                    )

        return cleaned_data


class AppointmentAdminForm(BaseAppointmentForm):
    """Форма записи для админки с выбором времени из списка"""

    appointment_time = forms.ChoiceField(
        choices=[],
        label="Время записи",
        help_text="Время с 10:00 до 19:00 с шагом 30 минут",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Генерируем список времени
        time_choices = []
        for hour in range(10, 20):
            for minute in (0, 30):
                if hour == 19 and minute == 30:
                    break
                time_str = f"{hour:02d}:{minute:02d}"
                time_choices.append((time_str, time_str))

        self.fields["appointment_time"].choices = [("", "---------")] + time_choices

        # Устанавливаем текущее значение
        if self.instance and self.instance.appointment_time:
            current_time = self.instance.appointment_time.strftime("%H:%M")
            self.initial["appointment_time"] = current_time

        # Устанавливаем минимальную дату
        today = timezone.now().date()
        self.fields["appointment_date"].widget = forms.DateInput(
            attrs={"type": "date", "min": today.isoformat()}
        )

    def clean_appointment_time(self):
        """Преобразуем строку времени в объект time"""
        time_str = self.cleaned_data.get("appointment_time")
        if not time_str:
            return None
        return validate_working_hours(time_str)


class AppointmentForm(BaseAppointmentForm):
    """Форма записи для фронтенда"""

    class Meta(BaseAppointmentForm.Meta):
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
