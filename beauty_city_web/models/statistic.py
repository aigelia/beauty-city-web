from django.db import models


class Statistic(models.Model):
    """Модель для хранения статистики"""

    date = models.DateField(unique=True, verbose_name="Дата")
    total_appointments = models.IntegerField(default=0, verbose_name="Всего записей")
    completed_appointments = models.IntegerField(
        default=0, verbose_name="Завершенные записи"
    )
    total_revenue = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Общая выручка"
    )
    new_clients = models.IntegerField(default=0, verbose_name="Новых клиентов")

    def __str__(self):
        return f"Статистика за {self.date}"

    class Meta:
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"
