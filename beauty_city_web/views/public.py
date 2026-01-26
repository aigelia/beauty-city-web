from django.shortcuts import render, redirect
from django.conf import settings
from ..models import Salon, Service, Master, Review
import json
from datetime import datetime


def index(request):
    salons = Salon.objects.filter(is_active=True)[:4]
    services = Service.objects.all()
    masters = Master.objects.filter(is_active=True)
    reviews = Review.objects.all()

    salons_for_map = []
    for salon in salons:
        salons_for_map.append(
            {
                "name": salon.name,
                "address": salon.address,
                "full_address": f"Москва, {salon.address}",
                "phone": str(salon.phone) if salon.phone else "",
                "working_hours": salon.working_hours,
            }
        )

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
    # Получаем все активные салоны
    salons = Salon.objects.filter(is_active=True)

    context = {
        "salons": salons,
    }
    return render(request, "service.html", context)


def service_finally(request):
    appointment_data = request.session.get("appointment_data", {})

    if not appointment_data:
        return redirect("beauty_city_web:service")

    salon = None
    service = None
    master = None

    try:
        salon = Salon.objects.get(id=appointment_data.get("salon_id"))
    except Salon.DoesNotExist:
        pass

    try:
        service = Service.objects.get(id=appointment_data.get("service_id"))
    except Service.DoesNotExist:
        pass

    try:
        master = Master.objects.get(id=appointment_data.get("master_id"))
    except Master.DoesNotExist:
        pass

    date_str = appointment_data.get("date")
    formatted_date = ""
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            months = {
                1: "января",
                2: "февраля",
                3: "марта",
                4: "апреля",
                5: "мая",
                6: "июня",
                7: "июля",
                8: "августа",
                9: "сентября",
                10: "октября",
                11: "ноября",
                12: "декабря",
            }
            formatted_date = f"{date_obj.day} {months[date_obj.month]}"
        except:
            formatted_date = date_str

    context = {
        "appointment_data": appointment_data,
        "salon": salon,
        "service": service,
        "master": master,
        "date": date_str,
        "formatted_date": formatted_date,
        "time": appointment_data.get("time"),
    }

    return render(request, "serviceFinally.html", context)
