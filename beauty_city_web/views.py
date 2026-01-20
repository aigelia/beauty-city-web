from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Appointment, Salon, Master, Service, Client, PromoCode
from .forms import AppointmentForm, PromoCodeForm, ClientForm
import calendar
import json


def index(request):
    return render(request, "index.html")


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
    return admin_dashboard(request)


def is_admin(user):
    return user.is_staff


@staff_member_required
def admin_dashboard(request):
    """Главная страница админ-панели с статистикой"""
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)

    if today.month == 12:
        last_day_of_month = today.replace(
            year=today.year + 1, month=1, day=1
        ) - timedelta(days=1)
    else:
        last_day_of_month = today.replace(month=today.month + 1, day=1) - timedelta(
            days=1
        )

    monthly_appointments = Appointment.objects.filter(
        appointment_date__range=[first_day_of_month, last_day_of_month]
    )

    monthly_revenue = (
        monthly_appointments.aggregate(total=Sum("final_price"))["total"] or 0
    )

    monthly_completed = monthly_appointments.filter(status__in=["completed"]).count()

    monthly_total = monthly_appointments.count()

    first_day_of_year = today.replace(month=1, day=1)
    yearly_appointments = Appointment.objects.filter(
        appointment_date__range=[first_day_of_year, last_day_of_month]
    )
    yearly_total = yearly_appointments.count()

    attendance_rate = 0
    if monthly_total > 0:
        attendance_rate = round((monthly_completed / monthly_total) * 100)

    recent_appointments = Appointment.objects.select_related(
        "client", "master", "service", "salon"
    ).order_by("-appointment_date", "-appointment_time")[:10]

    salon_stats = Salon.objects.annotate(
        appointment_count=Count(
            "appointments",
            filter=Q(
                appointments__appointment_date__range=[
                    first_day_of_month,
                    last_day_of_month,
                ]
            ),
        ),
        revenue=Sum(
            "appointments__final_price",
            filter=Q(
                appointments__appointment_date__range=[
                    first_day_of_month,
                    last_day_of_month,
                ]
            ),
        ),
    )

    master_stats = Master.objects.annotate(
        appointment_count=Count(
            "appointments",
            filter=Q(
                appointments__appointment_date__range=[
                    first_day_of_month,
                    last_day_of_month,
                ]
            ),
        ),
        revenue=Sum(
            "appointments__final_price",
            filter=Q(
                appointments__appointment_date__range=[
                    first_day_of_month,
                    last_day_of_month,
                ]
            ),
        ),
    ).order_by("-appointment_count")[:10]

    context = {
        "monthly_revenue": monthly_revenue,
        "monthly_appointments": monthly_total,
        "monthly_completed": monthly_completed,
        "attendance_rate": attendance_rate,
        "yearly_appointments": yearly_total,
        "recent_appointments": recent_appointments,
        "salon_stats": salon_stats,
        "master_stats": master_stats,
        "today": today,
    }

    return render(request, "admin.html", context)


@staff_member_required
def admin_appointments(request):
    """Управление записями"""
    status_filter = request.GET.get("status", "all")
    date_filter = request.GET.get("date", "")
    master_filter = request.GET.get("master", "")

    appointments = Appointment.objects.select_related(
        "client", "master", "service", "salon", "promo_code"
    ).order_by("-appointment_date", "-appointment_time")

    if status_filter != "all":
        appointments = appointments.filter(status=status_filter)

    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    if master_filter:
        appointments = appointments.filter(master_id=master_filter)

    masters = Master.objects.all()

    context = {
        "appointments": appointments,
        "masters": masters,
        "status_filter": status_filter,
        "date_filter": date_filter,
        "master_filter": master_filter,
        "status_choices": Appointment.STATUS_CHOICES,
    }

    return render(request, "admin_appointments.html", context)



@staff_member_required
def admin_appointment_detail(request, appointment_id=None):
    """Детальная информация о записи или создание новой"""
    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        form = AppointmentForm(instance=appointment)
    else:
        appointment = None
        form = AppointmentForm()

    # Получаем все промокоды для JavaScript
    promocodes = PromoCode.objects.all()

    # Получаем все услуги
    services = Service.objects.all()

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            return redirect("admin_appointments")

    # Создаем данные о промокодах для JavaScript
    promo_codes_data = {}
    for promo in promocodes:
        promo_codes_data[str(promo.id)] = {
            "discount_type": promo.discount_type,
            "discount_value": float(promo.discount_value),
            "is_valid": promo.is_valid(),
        }

    context = {
        "appointment": appointment,
        "form": form,
        "promo_codes_data": json.dumps(promo_codes_data),
    }

    return render(request, "admin_appointment_form.html", context)


@staff_member_required
def admin_promocodes(request):
    """Управление промокодами"""
    promocodes = PromoCode.objects.all().order_by("-valid_from")

    if request.method == "POST":
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("admin_promocodes")
    else:
        form = PromoCodeForm()

    context = {
        "promocodes": promocodes,
        "form": form,
    }

    return render(request, "admin_promocodes.html", context)


@staff_member_required
def admin_clients(request):
    """Управление клиентами"""
    search_query = request.GET.get("search", "")

    clients = Client.objects.all().order_by("-registration_date")

    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    context = {
        "clients": clients,
        "search_query": search_query,
    }

    return render(request, "admin_clients.html", context)


@staff_member_required
def admin_client_detail(request, client_id):
    """Детальная информация о клиенте"""
    client = get_object_or_404(Client, id=client_id)
    appointments = client.appointments.select_related(
        "master", "service", "salon"
    ).order_by("-appointment_date", "-appointment_time")

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect("admin_clients")
    else:
        form = ClientForm(instance=client)

    context = {
        "client": client,
        "appointments": appointments,
        "form": form,
        "total_spent": sum(
            a.final_price for a in appointments if a.status == "completed"
        ),
    }

    return render(request, "admin_client_detail.html", context)


@staff_member_required
def admin_reports(request):
    """Отчеты и аналитика"""

    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    salon_id = request.GET.get("salon", "")

    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today

    appointments = Appointment.objects.filter(
        appointment_date__range=[start_date, end_date]
    )

    if salon_id:
        appointments = appointments.filter(salon_id=salon_id)

    total_revenue = appointments.aggregate(total=Sum("final_price"))["total"] or 0

    total_appointments = appointments.count()
    completed_appointments = appointments.filter(status="completed").count()
    cancelled_appointments = appointments.filter(status="cancelled").count()

    salon_stats = Salon.objects.annotate(
        appointment_count=Count(
            "appointments",
            filter=Q(appointments__appointment_date__range=[start_date, end_date]),
        ),
        revenue=Sum(
            "appointments__final_price",
            filter=Q(appointments__appointment_date__range=[start_date, end_date]),
        ),
        completed_count=Count(
            "appointments",
            filter=Q(
                appointments__appointment_date__range=[start_date, end_date],
                appointments__status="completed",
            ),
        ),
    ).order_by("-revenue")

    master_stats = Master.objects.annotate(
        appointment_count=Count(
            "appointments",
            filter=Q(appointments__appointment_date__range=[start_date, end_date]),
        ),
        revenue=Sum(
            "appointments__final_price",
            filter=Q(appointments__appointment_date__range=[start_date, end_date]),
        ),
    ).order_by("-revenue")[:10]

    service_stats = Service.objects.annotate(
        appointment_count=Count(
            "appointments",
            filter=Q(appointments__appointment_date__range=[start_date, end_date]),
        ),
        revenue=Sum(
            "appointments__final_price",
            filter=Q(appointments__appointment_date__range=[start_date, end_date]),
        ),
    ).order_by("-revenue")[:10]

    daily_stats = []
    current_date = (
        datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(start_date, str)
        else start_date
    )
    end_date_obj = (
        datetime.strptime(end_date, "%Y-%m-%d").date()
        if isinstance(end_date, str)
        else end_date
    )

    while current_date <= end_date_obj:
        day_appointments = appointments.filter(appointment_date=current_date)
        day_revenue = day_appointments.aggregate(total=Sum("final_price"))["total"] or 0
        day_count = day_appointments.count()

        daily_stats.append(
            {
                "date": current_date,
                "revenue": day_revenue,
                "count": day_count,
            }
        )

        current_date += timedelta(days=1)

    salons = Salon.objects.all()

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "salon_id": salon_id,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "completed_appointments": completed_appointments,
        "cancelled_appointments": cancelled_appointments,
        "salon_stats": salon_stats,
        "master_stats": master_stats,
        "service_stats": service_stats,
        "daily_stats": daily_stats,
        "salons": salons,
    }

    return render(request, "admin_reports.html", context)


@staff_member_required
def admin_calendar(request):
    """Календарь записей"""
    year = request.GET.get("year", timezone.now().year)
    month = request.GET.get("month", timezone.now().month)

    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = timezone.now().year
        month = timezone.now().month

    appointments = Appointment.objects.filter(
        appointment_date__year=year, appointment_date__month=month
    ).select_related("client", "master", "service", "salon")

    appointments_by_date = {}
    for appointment in appointments:
        date_str = appointment.appointment_date.strftime("%Y-%m-%d")
        if date_str not in appointments_by_date:
            appointments_by_date[date_str] = []
        appointments_by_date[date_str].append(appointment)

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        "calendar": cal,
        "year": year,
        "month": month,
        "month_name": month_name,
        "appointments_by_date": appointments_by_date,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "today": timezone.now().date(),
    }

    return render(request, "admin_calendar.html", context)


@staff_member_required
def admin_settings(request):
    """Настройки системы"""
    # В будущем здесь можно добавить настройки системы
    return render(request, "admin_settings.html")
