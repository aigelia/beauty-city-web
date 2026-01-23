from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

app_name = "beauty_city_web"

urlpatterns = [
    # Публичные страницы
    path("", views.index, name="index"),
    path("service/", views.service, name="service"),
    path("service-finally/", views.service_finally, name="service_finally"),
    # API маршруты (для фронтенда)
    path("api/salons/", views.api_salons, name="api_salons"),
    path("api/services/", views.api_services, name="api_services"),
    path("api/masters/", views.api_masters, name="api_masters"),
    path("api/available-dates/", views.api_available_dates, name="api_available_dates"),
    path("api/available-times/", views.api_available_times, name="api_available_times"),
    path(
        "api/save-appointment/", views.api_save_appointment, name="api_save_appointment"
    ),
    path("api/check-promo/", views.api_check_promo, name="api_check_promo"),
    path(
        "api/create-appointment/",
        views.api_create_appointment,
        name="api_create_appointment",
    ),
    path(
        "api/appointment-details/",
        views.api_get_appointment_details,
        name="api_appointment_details",
    ),
    path(
        "api/client-statistics/",
        views.api_client_statistics,
        name="api_client_statistics",
    ),
    path("api/total-clients/", views.api_total_clients, name="api_total_clients"),
    path("api/contact-request/", views.api_contact_request, name="api_contact_request"),
]
