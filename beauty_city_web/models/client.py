from django.db import models


class Client(models.Model):
    """Модель клиента"""

    phone = models.CharField(max_length=20, unique=True, verbose_name="Телефон")
    name = models.CharField(max_length=100, verbose_name="Имя")
    email = models.EmailField(blank=True, verbose_name="Email")
    registration_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации"
    )

    def __str__(self):
        return f"{self.name} - {self.phone}"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
