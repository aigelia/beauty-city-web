from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class PromoCode(models.Model):
    """Модель промокода"""

    DISCOUNT_TYPES = [
        ("percent", "Процент"),
        ("fixed", "Фиксированная сумма"),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name="Код промокода")
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPES,
        default="percent",
        verbose_name="Тип скидки",
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Значение скидки"
    )
    description = models.CharField(max_length=200, verbose_name="Описание")
    valid_from = models.DateTimeField(verbose_name="Действует с")
    valid_to = models.DateTimeField(verbose_name="Действует до")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def is_valid(self):
        """Проверка валидности промокода"""
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_to

    def calculate_discount(self, price):
        """Расчет скидки на основе цены"""
        if not self.is_valid():
            return 0

        if self.discount_type == "percent":
            discount = price * (self.discount_value / 100)
        else:
            discount = min(price, self.discount_value)

        return discount

    def __str__(self):
        return f"{self.code} - {self.description}"

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
