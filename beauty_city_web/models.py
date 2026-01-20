from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


class Salon(models.Model):
    """Модель салона красоты"""

    name = models.CharField(max_length=200, verbose_name="Название салона")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    phone = models.CharField(
        max_length=20, verbose_name="Телефон", default="+7 (917) 902 38 00"
    )
    working_hours = models.CharField(
        max_length=100,
        verbose_name="Часы работы",
        default="с 10:00 до 20:00 без выходных",
    )
    photo = models.ImageField(
        upload_to="salons/", blank=True, null=True, verbose_name="Фото"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return f"{self.name} - {self.address}"

    class Meta:
        verbose_name = "Салон"
        verbose_name_plural = "Салоны"


class ServiceCategory(models.Model):
    """Категория услуг"""

    name = models.CharField(max_length=100, verbose_name="Название категории")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"


class Service(models.Model):
    """Модель услуги"""

    name = models.CharField(max_length=200, verbose_name="Название услуги")
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Категория",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    duration = models.IntegerField(
        verbose_name="Длительность (минуты)",
        help_text="Продолжительность услуги в минутах",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    photo = models.ImageField(
        upload_to="services/", blank=True, null=True, verbose_name="Фото"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    def __str__(self):
        return f"{self.name} - {self.price} руб."

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Master(models.Model):
    """Модель мастера"""

    name = models.CharField(max_length=100, verbose_name="Имя мастера")
    photo = models.ImageField(
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
        Salon, related_name="masters", verbose_name="Салоны"
    )
    services = models.ManyToManyField(
        Service, related_name="masters", verbose_name="Услуги"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    def __str__(self):
        return f"{self.name} - {self.specialty}"

    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"


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
    max_uses = models.IntegerField(
        default=1, verbose_name="Максимальное количество использований"
    )
    used_count = models.IntegerField(default=0, verbose_name="Количество использований")

    def save(self, *args, **kwargs):
        """Переопределяем save для проверки максимального использования"""

        if self.used_count > self.max_uses:
            raise ValidationError(
                f"Промокод уже использован максимальное количество раз ({self.max_uses})"
            )

        super().save(*args, **kwargs)

    def is_valid(self):
        """Проверка валидности промокода"""
        now = timezone.now()
        return (
            self.is_active
            and self.valid_from <= now <= self.valid_to
            and self.used_count < self.max_uses
        )

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
        Client,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Клиент",
    )
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Мастер",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Услуга",
    )
    salon = models.ForeignKey(
        Salon,
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
        PromoCode,
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
