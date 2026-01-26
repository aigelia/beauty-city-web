from phonenumbers import PhoneNumberFormat, format_number, parse, is_valid_number
from phonenumbers.phonenumberutil import NumberParseException
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q
from datetime import datetime, date, time as dt_time
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import Appointment, Salon, Master, Service, Client, PromoCode
from django.core.exceptions import ValidationError
from ..forms.client import ClientForm
from ..utils.validators import (
    validate_future_date,
    validate_working_hours,
    validate_appointment_datetime,
)


@csrf_exempt
def api_salons(request):
    """Получить список всех активных салонов"""
    try:
        salons = Salon.objects.filter(is_active=True)
        data = []
        for salon in salons:
            data.append(
                {
                    "id": salon.id,
                    "name": salon.name,
                    "address": salon.address,
                    "phone": str(salon.phone) if salon.phone else "",
                    "working_hours": salon.working_hours,
                    "photo_url": salon.photo.url if salon.photo else None,
                }
            )
        print(f"API Salons: Found {len(data)} salons")
        return JsonResponse({"salons": data})
    except Exception as e:
        print(f"API Salons Error: {str(e)}")
        return JsonResponse({"error": str(e), "salons": []}, status=500)


@csrf_exempt
def api_services(request):
    """Получить услуги с фильтрацией по салону и мастеру"""
    salon_id = request.GET.get("salon_id")
    master_id = request.GET.get("master_id")

    services = Service.objects.filter(is_active=True)

    if salon_id and salon_id != "any":
        services = services.filter(masters__salons__id=salon_id).distinct()

    if master_id and master_id != "any":
        services = services.filter(masters__id=master_id).distinct()

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

    return JsonResponse({"categories": list(categories.values())})


@csrf_exempt
def api_masters(request):
    """Получить мастеров с фильтрацией по салону и услуге"""
    salon_id = request.GET.get("salon_id")
    service_id = request.GET.get("service_id")

    masters = Master.objects.filter(is_active=True)

    if salon_id and salon_id != "any":
        masters = masters.filter(salons__id=salon_id).distinct()

    if service_id and service_id != "any":
        masters = masters.filter(services__id=service_id).distinct()

    data = []
    for master in masters:
        master_salons = master.salons.filter(is_active=True)
        salons_data = [
            {"id": salon.id, "name": salon.name, "address": salon.address}
            for salon in master_salons
        ]

        master_services = master.services.filter(is_active=True)
        services_data = [
            {"id": service.id, "name": service.name, "price": float(service.price)}
            for service in master_services
        ]

        data.append(
            {
                "id": master.id,
                "name": master.name,
                "specialty": master.specialty,
                "experience": master.experience,
                "rating": float(master.rating) if master.rating else 0.0,
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

    today = datetime.now().date()
    dates = []

    for i in range(30):
        date = today + timedelta(days=i)

        if master_id:
            try:
                master = Master.objects.get(id=master_id)
                available_services = master.get_available_services()
                if available_services:
                    service = available_services[0]
                    available_times = service.get_available_times(
                        date, master_id=master_id, salon_id=salon_id
                    )
                else:
                    available_times = []
            except Master.DoesNotExist:
                available_times = []
        else:
            available_times = []

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
def api_available_dates_simple(request):
    """Получить доступные даты без привязки к мастеру"""
    salon_id = request.GET.get("salon_id")
    service_id = request.GET.get("service_id")
    master_id = request.GET.get("master_id")

    today = datetime.now().date()
    dates = []

    if not any([salon_id, service_id, master_id]):
        for i in range(30):
            date_obj = today + timedelta(days=i)
            dates.append(
                {
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "day": date_obj.day,
                    "month": date_obj.strftime("%B"),
                    "weekday": date_obj.strftime("%A"),
                    "is_today": date_obj == today,
                    "is_tomorrow": date_obj == today + timedelta(days=1),
                }
            )
        return JsonResponse({"dates": dates})

    for i in range(30):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")

        appointments = Appointment.objects.filter(
            appointment_date=date_obj, status__in=["pending", "confirmed"]
        )

        if salon_id and salon_id != "any":
            appointments = appointments.filter(salon_id=salon_id)

        if service_id and service_id != "any":
            appointments = appointments.filter(service_id=service_id)

        if master_id and master_id != "any":
            appointments = appointments.filter(master_id=master_id)

        busy_times = set(appointments.values_list("appointment_time", flat=True))

        all_times = []
        for hour in range(10, 20):
            for minute in (0, 30):
                if hour == 19 and minute == 30:
                    break
                all_times.append(f"{hour:02d}:{minute:02d}")

        if len(busy_times) < len(all_times):
            dates.append(
                {
                    "date": date_str,
                    "day": date_obj.day,
                    "month": date_obj.strftime("%B"),
                    "weekday": date_obj.strftime("%A"),
                    "is_today": date_obj == today,
                    "is_tomorrow": date_obj == today + timedelta(days=1),
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

    today = datetime.now().date()
    if date < today:
        return JsonResponse({"times": []})

    times = []

    morning_times = []
    day_times = []
    evening_times = []

    # Рабочие часы: с 10:00 до 19:00, шаг 30 минут
    for hour in range(10, 20):
        for minute in (0, 30):
            if hour == 19 and minute == 30:
                break
            time_str = f"{hour:02d}:{minute:02d}"

            # Проверяем, свободно ли это время
            if master_id and master_id != "any":
                # Проверяем занятость у мастера
                appointments = Appointment.objects.filter(
                    master_id=master_id,
                    appointment_date=date,
                    appointment_time=time_str,
                    status__in=["pending", "confirmed"],
                )
                if appointments.exists():
                    continue

            if service_id and service_id != "any" and salon_id and salon_id != "any":
                appointments = Appointment.objects.filter(
                    service_id=service_id,
                    salon_id=salon_id,
                    appointment_date=date,
                    appointment_time=time_str,
                    status__in=["pending", "confirmed"],
                )
                if appointments.exists():
                    continue

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

    return JsonResponse({"times": times})


@csrf_exempt
def api_save_appointment(request):
    """Сохранить данные записи в сессии"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            appointment_data = {
                "salon_id": data.get("salon_id"),
                "service_id": data.get("service_id"),
                "master_id": data.get("master_id"),
                "date": data.get("date"),
                "time": data.get("time"),
            }

            # Сохраняем в сессии
            request.session["appointment_data"] = appointment_data
            request.session.modified = True

            return JsonResponse(
                {
                    "success": True,
                    "redirect_url": "/service-finally/",
                    "message": "Данные сохранены",
                }
            )
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
        is_valid = promo.is_valid()

        if is_valid:
            return JsonResponse(
                {
                    "valid": True,
                    "code": promo.code,
                    "discount_type": promo.discount_type,
                    "discount_value": float(promo.discount_value),
                    "description": promo.description,
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
            appointment_data = request.session.get("appointment_data", {})

            final_data = {**appointment_data, **data}

            required_fields = ["phone", "name", "date", "time"]
            missing_fields = [
                field for field in required_fields if not final_data.get(field)
            ]

            if missing_fields:
                return JsonResponse(
                    {
                        "error": f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
                    },
                    status=400,
                )

            phone = final_data.get("phone")
            name = final_data.get("name")

            form_data = {
                "phone": phone,
                "name": name,
                "email": final_data.get("email", ""),
            }
            form = ClientForm(form_data)

            if not form.is_valid():
                return JsonResponse({"error": form.errors.as_text()}, status=400)

            client, created = Client.objects.update_or_create(
                phone=phone,
                defaults={"name": name, "email": final_data.get("email", "")},
            )

            salon = None
            service = None
            master = None

            if final_data.get("salon_id"):
                try:
                    salon = Salon.objects.get(id=final_data.get("salon_id"))
                except Salon.DoesNotExist:
                    pass

            if final_data.get("service_id"):
                try:
                    service = Service.objects.get(id=final_data.get("service_id"))
                except Service.DoesNotExist:
                    pass

            if final_data.get("master_id"):
                try:
                    master = Master.objects.get(id=final_data.get("master_id"))
                except Master.DoesNotExist:
                    pass

            if not salon:
                salon = Salon.objects.filter(is_active=True).first()

            if not service:
                service = Service.objects.filter(is_active=True).first()

            if not master and service:
                masters = service.masters.filter(is_active=True)
                if masters.exists():
                    master = masters.first()

            try:
                if Appointment.objects.get(
                    master=master,
                    appointment_date=datetime.strptime(
                        final_data["date"], "%Y-%m-%d"
                    ).date(),
                    appointment_time=datetime.strptime(final_data["time"], "%H:%M").time(),
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Запись на это время не доступна для этого мастера.",
                        }
                    )
            except Appointment.DoesNotExist:
                ...

            appointment = Appointment.objects.create(
                client=client,
                master=master,
                service=service,
                salon=salon,
                appointment_date=datetime.strptime(
                    final_data["date"], "%Y-%m-%d"
                ).date(),
                appointment_time=datetime.strptime(final_data["time"], "%H:%M").time(),
                status="pending",
                original_price=service.price if service else 0,
                final_price=service.price if service else 0,
            )

            if "appointment_data" in request.session:
                del request.session["appointment_data"]

            return JsonResponse(
                {
                    "success": True,
                    "appointment_id": appointment.id,
                    "message": "Запись успешно создана!",
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Метод не разрешен"}, status=405)


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


@csrf_exempt
def api_client_statistics(request):
    """Получить статистику по клиентам"""

    period = request.GET.get("period", "all")

    stats = Client.get_registration_stats(period if period != "all" else None)

    today = timezone.now().date()

    today_count = Client.objects.filter(registration_date__date=today).count()

    week_ago = today - timedelta(days=7)
    weekly_count = Client.objects.filter(registration_date__date__gte=week_ago).count()

    month_ago = today - timedelta(days=30)
    active_clients = (
        Client.objects.filter(appointments__appointment_date__gte=month_ago)
        .distinct()
        .count()
    )

    response_data = {
        "total_clients": stats["total_count"],
        "today_registrations": today_count,
        "weekly_registrations": weekly_count,
        "active_clients": active_clients,
        "daily_stats": stats["daily_stats"],
        "period": period,
        "last_updated": timezone.now().isoformat(),
    }

    return JsonResponse(response_data)


@csrf_exempt
def api_total_clients(request):
    """Получить общее количество клиентов (простая версия для админки)"""

    total_clients = Client.objects.count()
    return JsonResponse(
        {
            "total_clients": total_clients,
            "message": f"Всего зарегистрировано клиентов: {total_clients}",
        }
    )


@csrf_exempt
def api_contact_request(request):
    """Создать заявку на консультацию с главной страницы"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            name = data.get("name")
            phone = data.get("phone")
            question = data.get("question", "")
            terms_agreed = data.get("terms_agreed")

            # Валидация через ClientForm
            form_data = {
                "phone": phone,
                "name": name,
                "email": "",
            }
            form = ClientForm(form_data)

            if not form.is_valid():
                errors = form.errors.as_data()
                if errors:
                    for field, error_list in errors.items():
                        first_error = error_list[0]
                        return JsonResponse(
                            {"success": False, "error": str(first_error)},
                            status=400,
                        )
                else:
                    return JsonResponse(
                        {"success": False, "error": "Неверные данные"},
                        status=400,
                    )

            if not terms_agreed:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Необходимо согласие с политикой конфиденциальности",
                    },
                    status=400,
                )

            # Проверка телефона через phonenumbers
            try:
                parsed_number = parse(phone, "RU")
                if not is_valid_number(parsed_number):
                    return JsonResponse(
                        {"success": False, "error": "Неверный номер телефона"},
                        status=400,
                    )
                phone = format_number(parsed_number, PhoneNumberFormat.E164)
            except NumberParseException:
                return JsonResponse(
                    {"success": False, "error": "Неверный формат телефона"},
                    status=400,
                )

            cleaned_data = form.cleaned_data

            client, created = Client.objects.update_or_create(
                phone=phone,
                defaults={"name": cleaned_data["name"]},
            )

            from ..models import Consultation

            consultation = Consultation.objects.create(
                client=client, notes=question, status="pending"
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Спасибо! Мы свяжемся с вами в ближайшее время.",
                    "consultation_id": consultation.id,
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)
