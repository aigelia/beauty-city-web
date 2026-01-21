from django.db import models


class ServiceCategory(models.Model):
    """Категория услуг"""

    name = models.CharField(max_length=100, verbose_name="Название категории")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"
