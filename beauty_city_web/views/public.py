from django.shortcuts import render
from django.conf import settings
from ..models import Salon, Service, Master, Review
import json


def index(request):
    salons = Salon.objects.filter(is_active=True)[:4]
    services = Service.objects.all()
    masters = Master.objects.all()
    reviews = Review.objects.all()

    # Подготавливаем данные салонов для карты прямо во вьюхе
    salons_for_map = []
    for salon in salons:
        salons_for_map.append({
            'name': salon.name,
            'address': salon.address,
            'full_address': f"Москва, {salon.address}",
            'phone': salon.phone,
            'working_hours': salon.working_hours,
        })

    context = {
        "salons": salons,
        "salons_json": json.dumps(salons_for_map, ensure_ascii=False),
        "yandex_maps_api_key": settings.YANDEX_MAPS_API_KEY,
        "empty_salons_count": max(0, 4 - len(salons)),
        "services": services,
        "masters": masters,
        "reviews": reviews,
    }
    return render(request, "index.html", context)


def service(request):
    return render(request, "service.html")


def service_finally(request):
    return render(request, "serviceFinally.html")
