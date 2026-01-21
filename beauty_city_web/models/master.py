from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Master(models.Model):
    """Модель мастера"""

    name = models.CharField(max_length=100, verbose_name="Имя мастера")
    photo = models.FileField(
        upload_to="masters/", blank=True, null=True, verbose_name="Фото"
    )
    specialty = models.CharField(max_length=200, verbose_name="Специальность")
    experience = models.CharField(max_length=50, verbose_name="Стаж работы")
    rating = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="Рейтинг",
    )
    salons = models.ManyToManyField(
        "Salon", related_name="masters", verbose_name="Салоны"
    )
    services = models.ManyToManyField(
        "Service", related_name="masters", verbose_name="Услуги"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    def get_available_dates(self, days_ahead=30):
        """Получить даты, когда мастер работает"""
        from datetime import datetime, timedelta

        dates = []
        today = datetime.now().date()

        for i in range(days_ahead):
            date = today + timedelta(days=i)
            dates.append(date)

        return dates

    def get_available_services(self, salon_id=None):
        """Получить услуги, которые предоставляет мастер"""
        services = self.services.filter(is_active=True)
        return services

    def __str__(self):
        return f"{self.name} - {self.specialty}"

    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"
