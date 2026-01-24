from phonenumbers import PhoneNumberFormat, format_number, parse, is_valid_number
from phonenumbers.phonenumberutil import NumberParseException
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
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
        services = services.filter(masters__salons__id=salon_id).distinct()
    if category_id:
        services = services.filter(category_id=category_id)

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

    if master_id and service_id:
        try:
            service = Service.objects.get(id=service_id)
            available_times = service.get_available_times(
                date, master_id=master_id, salon_id=salon_id
            )

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

            required_fields = ["salon_id", "service_id", "master_id", "date", "time"]
            for field in required_fields:
                if field not in data:
                    return JsonResponse(
                        {"error": f"Missing field: {field}"}, status=400
                    )

            request.session["appointment_data"] = data
            request.session.modified = True

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

            if not appointment_data:
                appointment_data = data.get("appointment_data", {})

            required_fields = [
                "salon_id",
                "service_id",
                "master_id",
                "date",
                "time",
                "phone",
                "name",
            ]

            # Проверяем наличие всех обязательных полей
            missing_fields = []
            for field in required_fields:
                if field not in data and field not in appointment_data:
                    missing_fields.append(field)

            if missing_fields:
                return JsonResponse(
                    {
                        "error": f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
                    },
                    status=400,
                )

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

            phone = data.get("phone")
            name = data.get("name")

            form_data = {
                "phone": phone,
                "name": name,
                "email": data.get("email", "")
                }
            form = ClientForm(form_data)

            if not form.is_valid():
                errors = form.errors.as_data()
                if errors:
                    for field, error_list in errors.items():
                        first_error = error_list[0]
                        return JsonResponse({"error": str(first_error)}, status=400)
                else:
                    return JsonResponse({"error": "Неверные данные"}, status=400)

            # Если валидация прошла, используем очищенные данные
            cleaned_data = form.cleaned_data
            client, created = Client.objects.get_or_create(
                phone=cleaned_data["phone"], 
                defaults={
                    "name": cleaned_data["name"],
                    "email": cleaned_data["email"]
                }
            )

            if not created and (client.name != cleaned_data["name"] or client.email != cleaned_data["email"]):
                client.name = cleaned_data["name"]
                client.email = cleaned_data["email"]
                client.save()

            if not phone or not name:
                return JsonResponse({"error": "Не указаны телефон или имя"}, status=400)

            try:
                parsed_number = parse(phone, "RU")
                if not is_valid_number(parsed_number):
                    return JsonResponse(
                        {"error": "Неверный номер телефона"}, status=400
                    )

                phone = format_number(parsed_number, PhoneNumberFormat.E164)
            except NumberParseException:
                return JsonResponse({"error": "Неверный формат телефона"}, status=400)

            client, created = Client.objects.get_or_create(
                phone=phone, defaults={"name": name}
            )

            if not created and client.name != name:
                client.name = name
                client.save()

            date_str = data.get("date") or appointment_data.get("date")
            time_str = data.get("time") or appointment_data.get("time")

            if not date_str or not time_str:
                return JsonResponse({"error": "Не указаны дата или время"}, status=400)

            try:
                appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                appointment_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                return JsonResponse(
                    {"error": "Неверный формат даты или времени"}, status=400
                )

            try:
                validate_future_date(appointment_date)
                validate_working_hours(appointment_time)
                validate_appointment_datetime(appointment_date, appointment_time)
            except ValidationError as e:
                return JsonResponse({"error": str(e)}, status=400)

            # Проверка на занятость времени у мастера
            existing_appointment = Appointment.objects.filter(
                master=master,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=["pending", "confirmed"],
            ).exists()

            if existing_appointment:
                return JsonResponse({"error": "Это время уже занято"}, status=400)

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

            promo_code = data.get("promo_code")
            if promo_code:
                try:
                    promo = PromoCode.objects.get(code=promo_code, is_active=True)
                    if promo.is_valid():
                        appointment.promo_code = promo
                        appointment.save()
                except PromoCode.DoesNotExist:
                    pass

            if "appointment_data" in request.session:
                del request.session["appointment_data"]

            return JsonResponse(
                {
                    "success": True,
                    "appointment_id": appointment.id,
                    "appointment_number": f"#{appointment.id:05d}",
                    "message": "Запись успешно создана!",
                    "client_name": client.name,
                    "client_phone": str(client.phone),
                    "appointment_date": appointment_date.strftime("%d.%m.%Y"),
                    "appointment_time": appointment_time.strftime("%H:%M"),
                    "service_name": service.name,
                    "master_name": master.name,
                    "salon_name": salon.name,
                }
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"error": f"Внутренняя ошибка сервера: {str(e)}"}, status=500
            )

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
