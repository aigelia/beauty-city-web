from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    client = models.ForeignKey(
        "Client", verbose_name="Клиент", on_delete=models.CASCADE
    )
    text = models.TextField("Содержание")
    date = models.DateField("Дата")
    master = models.ForeignKey(
        "Master",
        verbose_name="Мастер",
        related_name="reviews",
        on_delete=models.CASCADE,
    )
    rating = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="Оценка",
    )

    def __str__(self):
        return f"{self.client} - {self.date}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
