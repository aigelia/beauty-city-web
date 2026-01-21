from django.shortcuts import render
from ..models import Salon, Service, Master, Review


def index(request):
    salons = Salon.objects.filter(is_active=True)[:4]
    services = Service.objects.all()
    masters = Master.objects.all()
    reviews = Review.objects.all()

    context = {
        "salons": salons,
        "empty_salons_count": max(0, 4 - len(salons)),
        "services": services,
        "masters": masters,
        "reviews": reviews,
    }
    return render(request, "index.html", context)


def notes(request):
    return render(request, "notes.html")


def popup(request):
    return render(request, "popup.html")


def service(request):
    return render(request, "service.html")


def service_finally(request):
    return render(request, "serviceFinally.html")


def admin_page(request):
    """Перенаправление на новую админ-панель"""
    from .admin_views import admin_dashboard

    return admin_dashboard(request)


def is_admin(user):
    return user.is_staff
