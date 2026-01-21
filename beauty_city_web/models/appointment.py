from django.db import models


class Appointment(models.Model):
    """Модель записи на услугу"""

    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("confirmed", "Подтверждена"),
        ("completed", "Завершена"),
        ("cancelled", "Отменена"),
        ("no_show", "Не явился"),
    ]

    client = models.ForeignKey(
        "Client",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Клиент",
    )
    master = models.ForeignKey(
        "Master",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Мастер",
    )
    service = models.ForeignKey(
        "Service",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Услуга",
    )
    salon = models.ForeignKey(
        "Salon",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Салон",
    )
    appointment_date = models.DateField(verbose_name="Дата записи")
    appointment_time = models.TimeField(verbose_name="Время записи")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус"
    )
    promo_code = models.ForeignKey(
        "PromoCode",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Промокод",
        related_name="appointments",
    )
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Исходная цена"
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Сумма скидки"
    )
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Итоговая цена"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")

    def save(self, *args, **kwargs):
        """Переопределяем save для расчета цен"""

        if not self.original_price and self.service:
            self.original_price = self.service.price

        if self.promo_code and self.promo_code.is_valid():
            self.discount_amount = self.promo_code.calculate_discount(
                self.original_price
            )
        else:
            self.discount_amount = 0

        self.final_price = self.original_price - self.discount_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Запись #{self.id} - {self.client.name} - {self.service.name}"

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ["-id"]
