from .public import *
from .api import *

__all__ = [
    # Публичные представления
    "index",
    "service",
    "service_finally",
    "admin_page",
    "is_admin",
    # API представления
    "api_salons",
    "api_services",
    "api_masters",
    "api_available_dates",
    "api_available_dates_simple",
    "api_available_times",
    "api_save_appointment",
    "api_check_promo",
    "api_create_appointment",
    "api_get_appointment_details",
    "api_client_statistics",
    "api_total_clients",
    "api_contact_request",
]
