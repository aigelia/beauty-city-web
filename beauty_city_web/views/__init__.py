from .public import *
from .admin_views import *
from .api import *

__all__ = [
    # Публичные представления
    "index",
    "notes",
    "popup",
    "service",
    "service_finally",
    "admin_page",
    "is_admin",
    # Админ-представления
    "admin_dashboard",
    "admin_appointments",
    "admin_appointment_detail",
    "admin_clients",
    "admin_client_detail",
    "admin_promocodes",
    "admin_reports",
    "admin_calendar",
    "admin_settings",
    # API представления
    "api_salons",
    "api_services",
    "api_masters",
    "api_available_dates",
    "api_available_times",
    "api_save_appointment",
    "api_check_promo",
    "api_create_appointment",
    "api_get_appointment_details",
]
