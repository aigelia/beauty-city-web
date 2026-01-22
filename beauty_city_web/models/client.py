from django.db import models
from django.db.models import Count, Q
from datetime import date, timedelta


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

    @classmethod
    def get_registration_stats(cls, period=None):
        """
        Получить статистику регистраций клиентов
        period: 'today', 'week', 'month', 'year' или None (все время)
        """
        queryset = cls.objects.all()

        if period:
            today = date.today()

            if period == "today":
                queryset = queryset.filter(registration_date__date=today)
            elif period == "week":
                week_ago = today - timedelta(days=7)
                queryset = queryset.filter(registration_date__date__gte=week_ago)
            elif period == "month":
                month_ago = today - timedelta(days=30)
                queryset = queryset.filter(registration_date__date__gte=month_ago)
            elif period == "year":
                year_ago = today - timedelta(days=365)
                queryset = queryset.filter(registration_date__date__gte=year_ago)

        total_count = queryset.count()

        thirty_days_ago = today - timedelta(days=30)
        daily_stats = (
            queryset.filter(registration_date__date__gte=thirty_days_ago)
            .extra(select={"day": "DATE(registration_date)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return {"total_count": total_count, "daily_stats": list(daily_stats)}
