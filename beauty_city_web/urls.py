from django.urls import path
from . import views

app_name = 'beauty_city_web'

urlpatterns = [
    path('', views.index, name='index'),
    path('notes/', views.notes, name='notes'),
    path('popup/', views.popup, name='popup'),
    path('service/', views.service, name='service'),
    path('service-finally/', views.service_finally, name='service_finally'),
    path('admin-page/', views.admin_page, name='admin_page'),
]
