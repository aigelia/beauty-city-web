from django.db import models
from .servicecategory import ServiceCategory
from .appointment import Appointment


class Service(models.Model):
    """Модель услуги"""

    name = models.CharField(max_length=200, verbose_name="Название услуги")
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Категория",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    duration = models.IntegerField(
        verbose_name="Длительность (минуты)",
        help_text="Продолжительность услуги в минутах",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    photo = models.FileField(
        upload_to="services/", blank=True, null=True, verbose_name="Фото"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    def get_available_masters(self, salon_id=None):
        """Получить мастеров, которые предоставляют эту услугу"""
        masters = self.masters.filter(is_active=True)
        if salon_id:
            masters = masters.filter(salons__id=salon_id)
        return masters

    def get_available_times(self, date, master_id=None, salon_id=None):
        """Получить доступное время для услуги"""
        from datetime import datetime, timedelta
        import pytz

        # Базовые рабочие часы
        start_time = datetime.strptime("10:00", "%H:%M").time()
        end_time = datetime.strptime("19:00", "%H:%M").time()

        # Все возможные слоты
        slots = []
        current = datetime.combine(date, start_time)
        end = datetime.combine(date, end_time)

        while current < end:
            slots.append(current.time())
            current += timedelta(minutes=30)

        # Получаем занятые слоты
        appointments = Appointment.objects.filter(
            appointment_date=date, status__in=["pending", "confirmed"]
        )

        if master_id:
            appointments = appointments.filter(master_id=master_id)
        if salon_id:
            appointments = appointments.filter(salon_id=salon_id)

        busy_times = [a.appointment_time for a in appointments]

        # Фильтруем свободные слоты
        available_slots = []
        for slot in slots:
            if slot not in busy_times:
                # Проверяем, что слот не в прошлом (для сегодняшней даты)
                now = datetime.now(pytz.timezone("Europe/Moscow"))
                slot_datetime = datetime.combine(date, slot)
                slot_datetime = pytz.timezone("Europe/Moscow").localize(slot_datetime)

                if slot_datetime > now + timedelta(hours=1):
                    available_slots.append(slot.strftime("%H:%M"))

        return available_slots

    def __str__(self):
        return f"{self.name} - {self.price} руб."

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
