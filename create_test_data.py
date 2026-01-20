import os
import django
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from beauty_city_web.models import (
    Salon,
    ServiceCategory,
    Service,
    Master,
    Client,
    PromoCode,
    Appointment,
)
from django.utils import timezone


def create_test_data():
    print("Создание тестовых данных...")

    salons = [
        Salon(name="BeautyCity Пушкинская", address="ул. Пушкинская, д. 78А"),
        Salon(name="BeautyCity Ленина", address="ул. Ленина, д. 211"),
        Salon(name="BeautyCity Красная", address="ул. Красная, д. 10"),
    ]
    for salon in salons:
        salon.save()
    print(f"Создано салонов: {len(salons)}")

    categories = [
        ServiceCategory(name="Макияж", order=1),
        ServiceCategory(name="Парикмахерские услуги", order=2),
        ServiceCategory(name="Ногтевой сервис", order=3),
    ]
    for category in categories:
        category.save()
    print(f"Создано категорий: {len(categories)}")

    services = [
        Service(name="Дневной макияж", category=categories[0], price=1400, duration=60),
        Service(
            name="Свадебный макияж", category=categories[0], price=3000, duration=90
        ),
        Service(
            name="Вечерний макияж", category=categories[0], price=2000, duration=75
        ),
        Service(
            name="Окрашивание волос", category=categories[1], price=5000, duration=120
        ),
        Service(name="Укладка волос", category=categories[1], price=1500, duration=60),
        Service(
            name="Маникюр. Классический. Гель",
            category=categories[2],
            price=2000,
            duration=90,
        ),
        Service(name="Педикюр", category=categories[2], price=1000, duration=60),
    ]
    for service in services:
        service.save()
    print(f"Создано услуг: {len(services)}")

    masters = [
        Master(
            name="Елизавета Лапина",
            specialty="Мастер маникюра",
            experience="3 г. 10 мес.",
            rating=4.8,
        ),
        Master(
            name="Анастасия Сергеева",
            specialty="Парикмахер",
            experience="4 г. 9 мес.",
            rating=4.9,
        ),
        Master(
            name="Ева Колесова",
            specialty="Визажист",
            experience="1 г. 2 мес.",
            rating=4.7,
        ),
        Master(
            name="Мария Суворова",
            specialty="Стилист",
            experience="1 г. 1 мес.",
            rating=4.6,
        ),
    ]
    for master in masters:
        master.save()
        master.salons.set(salons)

        if "маникюр" in master.specialty.lower():
            master.services.set(
                [
                    s
                    for s in services
                    if "маникюр" in s.name.lower() or "педикюр" in s.name.lower()
                ]
            )
        elif "парикмахер" in master.specialty.lower():
            master.services.set([s for s in services if "волос" in s.name.lower()])
        elif "визажист" in master.specialty.lower():
            master.services.set([s for s in services if "макияж" in s.name.lower()])
        else:
            master.services.set(services[:3])
    print(f"Создано мастеров: {len(masters)}")

    clients = [
        Client(name="Алиса И.", phone="+79179023800", email="alice@example.com"),
        Client(name="Светлана Г.", phone="+79179023801", email="svetlana@example.com"),
        Client(name="Ольга Н.", phone="+79179023802", email="olga@example.com"),
        Client(name="Елена В.", phone="+79179023803", email="elena@example.com"),
        Client(name="Виктория Г.", phone="+79179023804", email="victoria@example.com"),
    ]
    for client in clients:
        client.save()
    print(f"Создано клиентов: {len(clients)}")

    now = timezone.now()
    promocodes = [
        PromoCode(
            code="KID20",
            discount_type="percent",
            discount_value=20,
            description="Для беременных мам",
            valid_from=now - timedelta(days=30),
            valid_to=now + timedelta(days=365),
            max_uses=100,
        ),
        PromoCode(
            code="BIRTHDAY",
            discount_type="percent",
            discount_value=15,
            description="В честь дня рождения",
            valid_from=now - timedelta(days=30),
            valid_to=now + timedelta(days=365),
            max_uses=100,
        ),
        PromoCode(
            code="MAN10",
            discount_type="percent",
            discount_value=10,
            description="Для мужчин в декабре",
            valid_from=now.replace(month=12, day=1),
            valid_to=now.replace(month=12, day=31),
            max_uses=50,
        ),
    ]
    for promo in promocodes:
        promo.save()
    print(f"Создано промокодов: {len(promocodes)}")

    appointments = []
    today = timezone.now().date()

    for i in range(10):
        appointment = Appointment(
            client=clients[i % len(clients)],
            master=masters[i % len(masters)],
            service=services[i % len(services)],
            salon=salons[i % len(salons)],
            appointment_date=today - timedelta(days=i + 1),
            appointment_time=datetime.strptime(f"{10 + (i % 6)}:00", "%H:%M").time(),
            status=(
                "completed" if i % 3 == 0 else "cancelled" if i % 3 == 1 else "no_show"
            ),
            promo_code=promocodes[0] if i % 4 == 0 else None,
        )
        appointment.save()
        appointments.append(appointment)

    for i in range(5):
        appointment = Appointment(
            client=clients[i % len(clients)],
            master=masters[i % len(masters)],
            service=services[i % len(services)],
            salon=salons[i % len(salons)],
            appointment_date=today + timedelta(days=i + 1),
            appointment_time=datetime.strptime(f"{14 + (i % 4)}:00", "%H:%M").time(),
            status="pending" if i % 2 == 0 else "confirmed",
            promo_code=promocodes[1] if i % 3 == 0 else None,
        )
        appointment.save()
        appointments.append(appointment)

    print(f"Создано записей: {len(appointments)}")
    print("Тестовые данные успешно созданы!")


if __name__ == "__main__":
    create_test_data()
