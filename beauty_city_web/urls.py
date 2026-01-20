from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

app_name = "beauty_city_web"

urlpatterns = [
    # Публичные страницы
    path("", views.index, name="index"),
    path("notes/", views.notes, name="notes"),
    path("popup/", views.popup, name="popup"),
    path("service/", views.service, name="service"),
    path("service-finally/", views.service_finally, name="service_finally"),
    # Старая админка (шаблон admin.html)
    path("admin-page/", views.admin_page, name="admin_page"),
    # Новая админ-панель (защищена аутентификацией)
    path(
        "admin/dashboard/",
        login_required(views.admin_dashboard),
        name="admin_dashboard",
    ),
    path(
        "admin/appointments/",
        login_required(views.admin_appointments),
        name="admin_appointments",
    ),
    path(
        "admin/appointments/<int:appointment_id>/",
        login_required(views.admin_appointment_detail),
        name="admin_appointment_detail",
    ),
    path("admin/clients/", login_required(views.admin_clients), name="admin_clients"),
    path(
        "admin/clients/<int:client_id>/",
        login_required(views.admin_client_detail),
        name="admin_client_detail",
    ),
    path(
        "admin/promocodes/",
        login_required(views.admin_promocodes),
        name="admin_promocodes",
    ),
    path("admin/reports/", login_required(views.admin_reports), name="admin_reports"),
    path(
        "admin/calendar/", login_required(views.admin_calendar), name="admin_calendar"
    ),
    path(
        "admin/settings/", login_required(views.admin_settings), name="admin_settings"
    ),
    # Аутентификация
    path(
        "admin/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="admin_login",
    ),
    path("admin/logout/", auth_views.LogoutView.as_view(), name="admin_logout"),
    path(
        "admin/appointments/new/",
        login_required(views.admin_appointment_detail),
        name="admin_appointment_create",
    ),
]
