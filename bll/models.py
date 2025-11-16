from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class BookingStatus(str, Enum):
    
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass
class Hotel:
    
    id: int                  # унікальний ідентифікатор
    name: str                # назва готелю
    city: str                # місто
    address: str             # адреса
    description: str         # короткий опис


@dataclass
class Room:
   
    id: int                  # унікальний ідентифікатор кімнати
    hotel_id: int            # ID готелю, якому належить кімната
    number: str              # "101", "203A" тощо
    capacity: int            # кількість місць у номері
    price_per_night: float   # ціна за одну добу


@dataclass
class Client:
   
    id: int
    first_name: str
    last_name: str
    phone: str
    email: str


@dataclass
class Booking:
   
    id: int
    hotel_id: int
    room_id: int
    client_id: int

    check_in: date           # дата заїзду
    check_out: date          # дата виїзду

    status: BookingStatus    # статус заявки / бронювання
    request_text: str = ""   # текст заявки (побажання тощо)

    def duration_days(self) -> int:
        
        return (self.check_out - self.check_in).days
