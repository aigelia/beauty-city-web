from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Salon(models.Model):
    """Модель салона красоты"""

    name = models.CharField(max_length=200, verbose_name="Название салона")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    phone = PhoneNumberField(
        verbose_name="Телефон",
        default="+79179023800",
        region="RU",
    )
    working_hours = models.CharField(
        max_length=100,
        verbose_name="Часы работы",
        default="с 10:00 до 20:00 без выходных",
    )
    photo = models.FileField(
        upload_to="salons/", blank=True, null=True, verbose_name="Фото"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return f"{self.name} - {self.address}"

    class Meta:
        verbose_name = "Салон"
        verbose_name_plural = "Салоны"
