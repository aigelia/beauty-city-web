from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


def validate_future_date(date_value):
    """Валидация даты - нельзя выбирать прошедшие дни"""
    if date_value and date_value < timezone.now().date():
        raise ValidationError("Нельзя выбрать прошедшую дату")
    return date_value


def validate_working_hours(time_value):
    """Валидация времени: 10:00-19:00 с шагом 30 минут"""
    if time_value:
        if isinstance(time_value, str):
            try:
                hour, minute = map(int, time_value.split(":"))
                time_value = datetime.time(hour, minute)
            except (ValueError, TypeError):
                raise ValidationError("Неверный формат времени")

        hour = time_value.hour
        minute = time_value.minute

        if hour < 10 or hour > 19:
            raise ValidationError("Время должно быть с 10:00 до 19:00")

        if minute not in [0, 30]:
            raise ValidationError(
                "Время должно быть с шагом 30 минут (например: 10:00, 10:30, 11:00)"
            )
    return time_value


def validate_appointment_datetime(date_value, time_value):
    """Общая валидация даты и времени записи"""
    if date_value and time_value:
        now = timezone.now()

        if isinstance(time_value, str):
            try:
                hour, minute = map(int, time_value.split(":"))
                time_value = datetime.time(hour, minute)
            except (ValueError, TypeError):
                return

        selected_datetime = datetime.datetime.combine(
            date_value,
            time_value,
            tzinfo=timezone.get_current_timezone(),
        )

        if selected_datetime < now:
            raise ValidationError("Нельзя записаться на прошедшее время")

        if date_value == now.date():
            min_datetime = now + datetime.timedelta(hours=1)
            if selected_datetime < min_datetime:
                raise ValidationError(
                    f"При записи на сегодня минимальное время через 1 час"
                )
