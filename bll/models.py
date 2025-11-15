from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class BookingStatus(str, Enum):
    """
    Статус бронювання / заявки.
    PENDING    – заявка, ще не підтверджена.
    CONFIRMED  – підтверджене бронювання.
    CANCELLED  – скасоване бронювання.
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass
class Hotel:
    """
    Готель.
    room'и зберігатимуться окремо (через Room і репозиторій),
    тут мінімальна інформація про сам готель.
    """
    id: int                  # унікальний ідентифікатор
    name: str                # назва готелю
    city: str                # місто
    address: str             # адреса
    description: str         # короткий опис


@dataclass
class Room:
    """
    Номер у готелі.
    Один готель має багато кімнат.
    """
    id: int                  # унікальний ідентифікатор кімнати
    hotel_id: int            # ID готелю, якому належить кімната
    number: str              # "101", "203A" тощо
    capacity: int            # кількість місць у номері
    price_per_night: float   # ціна за одну добу


@dataclass
class Client:
    """
    Клієнт, який може бронювати номери в готелі.
    """
    id: int
    first_name: str
    last_name: str
    phone: str
    email: str


@dataclass
class Booking:
    """
    Заявка / бронювання номера в готелі.
    Використовуємо один клас для всього:
    - заявка:  status = PENDING
    - підтверджене бронювання: status = CONFIRMED
    - скасоване бронювання:    status = CANCELLED
    """
    id: int
    hotel_id: int
    room_id: int
    client_id: int

    check_in: date           # дата заїзду
    check_out: date          # дата виїзду

    status: BookingStatus    # статус заявки / бронювання
    request_text: str = ""   # текст заявки (побажання тощо)

    def duration_days(self) -> int:
        """
        Кількість діб проживання.
        Використовуватиметься для розрахунку вартості.
        """
        return (self.check_out - self.check_in).days
