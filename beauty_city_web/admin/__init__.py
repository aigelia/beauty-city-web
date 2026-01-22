from django.contrib import admin
from .salon import SalonAdmin
from .service import ServiceCategoryAdmin, ServiceAdmin
from .master import MasterAdmin
from .client import ClientAdmin
from .promocode import PromoCodeAdmin
from .appointment import AppointmentAdmin
from .statistic import StatisticAdmin
from .review import ReviewAdmin
from .consultation import ConsultationAdmin

from ..models import (
    Salon,
    ServiceCategory,
    Service,
    Master,
    Client,
    PromoCode,
    Appointment,
    Statistic,
    Review,
    Consultation,
)

# Регистрация моделей в админке
admin.site.register(Salon, SalonAdmin)
admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Master, MasterAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Statistic, StatisticAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Consultation, ConsultationAdmin)

# Настройка админ-панели
admin.site.site_header = "BeautyCity Администрация"
admin.site.site_title = "BeautyCity Админ"
admin.site.index_title = "Панель управления BeautyCity"
