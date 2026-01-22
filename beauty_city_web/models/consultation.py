from django.db import models


class Consultation(models.Model):
    """Модель записи на консультацию"""

    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("completed", "Завершена"),
    ]

    client = models.ForeignKey(
        "Client",
        on_delete=models.CASCADE,
        related_name="consultations",
        verbose_name="Клиент",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")

    def __str__(self):
        return f"Консультацию для {self.client.name} - {self.status}"

    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"
        ordering = ["-id"]
