from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta
from ..models import Appointment, Salon, Master, Service, Client, PromoCode
from django.utils import timezone


@csrf_exempt
def api_salons(request):
    """Получить список всех активных салонов"""
    salons = Salon.objects.filter(is_active=True)

    data = []
    for salon in salons:
        data.append(
            {
                "id": salon.id,
                "name": salon.name,
                "address": salon.address,
                "phone": salon.phone,
                "working_hours": salon.working_hours,
                "photo_url": salon.photo.url if salon.photo else None,
            }
        )

    return JsonResponse({"salons": data})


@csrf_exempt
def api_services(request):
    """Получить услуги с фильтрацией по салону"""
    salon_id = request.GET.get("salon_id")
    category_id = request.GET.get("category_id")

    services = Service.objects.filter(is_active=True)

    if salon_id:
        # Фильтруем услуги, доступные в выбранном салоне
        services = services.filter(masters__salons__id=salon_id).distinct()

    if category_id:
        services = services.filter(category_id=category_id)

    # Группируем по категориям
    categories = {}
    for service in services:
        category_name = service.category.name
        if category_name not in categories:
            categories[category_name] = {
                "id": service.category.id,
                "name": category_name,
                "services": [],
            }

        categories[category_name]["services"].append(
            {
                "id": service.id,
                "name": service.name,
                "price": float(service.price),
                "duration": service.duration,
                "photo_url": service.photo.url if service.photo else None,
            }
        )

    # Преобразуем словарь в список
    categories_list = list(categories.values())

    return JsonResponse({"categories": categories_list})


@csrf_exempt
def api_masters(request):
    """Получить мастеров с фильтрацией"""
    salon_id = request.GET.get("salon_id")
    service_id = request.GET.get("service_id")

    masters = Master.objects.filter(is_active=True)

    if salon_id:
        masters = masters.filter(salons__id=salon_id)

    if service_id:
        masters = masters.filter(services__id=service_id)

    data = []
    for master in masters:
        # Получаем салоны, где работает мастер
        master_salons = master.salons.filter(is_active=True)
        salons_data = []
        for salon in master_salons:
            salons_data.append(
                {
                    "id": salon.id,
                    "name": salon.name,
                    "address": salon.address,
                }
            )

        # Получаем услуги мастера
        master_services = master.services.filter(is_active=True)
        services_data = []
        for service in master_services:
            services_data.append(
                {
                    "id": service.id,
                    "name": service.name,
                    "price": float(service.price),
                }
            )

        data.append(
            {
                "id": master.id,
                "name": master.name,
                "specialty": master.specialty,
                "experience": master.experience,
                "rating": float(master.rating),
                "photo_url": master.photo.url if master.photo else None,
                "salons": salons_data,
                "services": services_data,
            }
        )

    return JsonResponse({"masters": data})


@csrf_exempt
def api_available_dates(request):
    """Получить доступные даты для записи"""
    master_id = request.GET.get("master_id")
    salon_id = request.GET.get("salon_id")

    # Генерируем даты на 30 дней вперед
    today = datetime.now().date()
    dates = []

    for i in range(30):
        date = today + timedelta(days=i)

        # Проверяем, есть ли доступные слоты на эту дату
        if master_id:
            master = Master.objects.get(id=master_id)
            available_times = (
                master.get_available_services()[0].get_available_times(
                    date, master_id=master_id, salon_id=salon_id
                )
                if master.get_available_services()
                else []
            )
        else:
            available_times = []

        # Если есть хотя бы один доступный слот, добавляем дату
        if not master_id or available_times:
            dates.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "day": date.day,
                    "month": date.strftime("%B"),
                    "weekday": date.strftime("%A"),
                    "is_today": date == today,
                    "is_tomorrow": date == today + timedelta(days=1),
                }
            )

    return JsonResponse({"dates": dates})


@csrf_exempt
def api_available_times(request):
    """Получить доступное время на выбранную дату"""
    date_str = request.GET.get("date")
    master_id = request.GET.get("master_id")
    service_id = request.GET.get("service_id")
    salon_id = request.GET.get("salon_id")

    if not date_str:
        return JsonResponse({"error": "Date is required"}, status=400)

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    # Проверяем, что дата не в прошлом
    today = datetime.now().date()
    if date < today:
        return JsonResponse({"times": []})

    times = []

    if master_id and service_id:
        try:
            service = Service.objects.get(id=service_id)
            available_times = service.get_available_times(
                date, master_id=master_id, salon_id=salon_id
            )

            # Группируем по времени суток
            morning_times = []
            day_times = []
            evening_times = []

            for time_str in available_times:
                hour = int(time_str.split(":")[0])
                if hour < 12:
                    morning_times.append(time_str)
                elif hour < 17:
                    day_times.append(time_str)
                else:
                    evening_times.append(time_str)

            if morning_times:
                times.append({"period": "Утро", "times": morning_times})
            if day_times:
                times.append({"period": "День", "times": day_times})
            if evening_times:
                times.append({"period": "Вечер", "times": evening_times})

        except (Service.DoesNotExist, Master.DoesNotExist):
            pass

    return JsonResponse({"times": times})


@csrf_exempt
def api_save_appointment(request):
    """Сохранить данные записи в сессии"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Валидация данных
            required_fields = ["salon_id", "service_id", "master_id", "date", "time"]
            for field in required_fields:
                if field not in data:
                    return JsonResponse(
                        {"error": f"Missing field: {field}"}, status=400
                    )

            # Сохраняем в сессии
            request.session["appointment_data"] = data
            request.session.modified = True

            # Также сохраняем отдельные поля для быстрого доступа
            for key, value in data.items():
                request.session[f"appointment_{key}"] = value

            return JsonResponse({"success": True, "redirect_url": "/service-finally/"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_check_promo(request):
    """Проверить промокод"""
    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "Code is required"}, status=400)

    try:
        promo = PromoCode.objects.get(code=code, is_active=True)

        # Проверяем валидность
        now = timezone.now()
        is_valid = promo.is_valid()

        if is_valid:
            return JsonResponse(
                {
                    "valid": True,
                    "code": promo.code,
                    "discount_type": promo.discount_type,
                    "discount_value": float(promo.discount_value),
                    "description": promo.description,
                    "max_uses": promo.max_uses,
                    "used_count": promo.used_count,
                }
            )
        else:
            return JsonResponse({"valid": False, "error": "Промокод недействителен"})

    except PromoCode.DoesNotExist:
        return JsonResponse({"valid": False, "error": "Промокод не найден"})


@csrf_exempt
def api_create_appointment(request):
    """Создать запись"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Получаем данные из сессии или из запроса
            appointment_data = request.session.get("appointment_data", {})
            if not appointment_data:
                appointment_data = data.get("appointment_data", {})

            # Обязательные поля
            required_fields = [
                "salon_id",
                "service_id",
                "master_id",
                "date",
                "time",
                "phone",
                "name",
            ]
            for field in required_fields:
                if field not in data and field not in appointment_data:
                    return JsonResponse(
                        {"error": f"Missing field: {field}"}, status=400
                    )

            # Получаем объекты из БД
            try:
                salon = Salon.objects.get(
                    id=data.get("salon_id") or appointment_data.get("salon_id")
                )
                service = Service.objects.get(
                    id=data.get("service_id") or appointment_data.get("service_id")
                )
                master = Master.objects.get(
                    id=data.get("master_id") or appointment_data.get("master_id")
                )
            except (Salon.DoesNotExist, Service.DoesNotExist, Master.DoesNotExist) as e:
                return JsonResponse({"error": str(e)}, status=400)

            # Находим или создаем клиента
            phone = data.get("phone")
            name = data.get("name")

            client, created = Client.objects.get_or_create(
                phone=phone, defaults={"name": name}
            )

            if not created and client.name != name:
                client.name = name
                client.save()

            # Создаем запись
            appointment_date = datetime.strptime(
                data.get("date") or appointment_data.get("date"), "%Y-%m-%d"
            ).date()

            appointment_time = datetime.strptime(
                data.get("time") or appointment_data.get("time"), "%H:%M"
            ).time()

            # Проверяем, не занято ли время
            existing_appointment = Appointment.objects.filter(
                master=master,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=["pending", "confirmed"],
            ).exists()

            if existing_appointment:
                return JsonResponse({"error": "Это время уже занято"}, status=400)

            # Создаем запись
            appointment = Appointment.objects.create(
                client=client,
                master=master,
                service=service,
                salon=salon,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status="pending",
                original_price=service.price,
                final_price=service.price,
            )

            # Применяем промокод если есть
            promo_code = data.get("promo_code")
            if promo_code:
                try:
                    promo = PromoCode.objects.get(code=promo_code, is_active=True)
                    if promo.is_valid():
                        appointment.promo_code = promo
                        appointment.discount_amount = promo.calculate_discount(
                            service.price
                        )
                        appointment.final_price = (
                            service.price - appointment.discount_amount
                        )
                        appointment.save()

                        # Увеличиваем счетчик использований
                        promo.used_count += 1
                        promo.save()
                except PromoCode.DoesNotExist:
                    pass

            # Очищаем сессию
            if "appointment_data" in request.session:
                del request.session["appointment_data"]

            return JsonResponse(
                {
                    "success": True,
                    "appointment_id": appointment.id,
                    "appointment_number": f"#{appointment.id:05d}",
                    "message": "Запись успешно создана!",
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_get_appointment_details(request):
    """Получить детали записи для страницы подтверждения"""
    appointment_data = request.session.get("appointment_data", {})

    if not appointment_data:
        return JsonResponse({"error": "No appointment data"}, status=400)

    try:
        salon = Salon.objects.get(id=appointment_data.get("salon_id"))
        service = Service.objects.get(id=appointment_data.get("service_id"))
        master = Master.objects.get(id=appointment_data.get("master_id"))

        data = {
            "salon": {
                "name": salon.name,
                "address": salon.address,
            },
            "service": {
                "name": service.name,
                "price": float(service.price),
                "duration": service.duration,
            },
            "master": {
                "name": master.name,
                "photo_url": master.photo.url if master.photo else None,
            },
            "date": appointment_data.get("date"),
            "time": appointment_data.get("time"),
        }

        return JsonResponse(data)

    except (Salon.DoesNotExist, Service.DoesNotExist, Master.DoesNotExist) as e:
        return JsonResponse({"error": str(e)}, status=400)
