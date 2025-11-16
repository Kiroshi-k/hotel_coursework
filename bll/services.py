from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Generic, TypeVar, List, Optional, Tuple, Set

from .models import Hotel, Room, Client, Booking, BookingStatus
from .exceptions import ValidationError, NotFoundError


T = TypeVar("T")


class IRepository(ABC, Generic[T]):
   

    @abstractmethod
    def get_all(self) -> List[T]:
        
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, id_: int) -> Optional[T]:
        
        raise NotImplementedError

    @abstractmethod
    def save_all(self, items: List[T]) -> None:
       
        raise NotImplementedError


class BaseService(Generic[T], ABC):
   

    def __init__(self, repo: IRepository[T]):
        self._repo = repo

    def _get_all(self) -> List[T]:
        return self._repo.get_all()

    def _save_all(self, items: List[T]) -> None:
        self._repo.save_all(items)

    def _generate_id(self) -> int:
        items = self._repo.get_all()
        if not items:
            return 1
        return max(getattr(item, "id") for item in items) + 1

    def _find_by_id_or_raise(self, id_: int, not_found_message: str) -> T:
        item = self._repo.get_by_id(id_)
        if item is None:
            raise NotFoundError(not_found_message)
        return item


class HotelService(BaseService[Hotel]):
   

    def add_hotel(self, name: str, city: str, address: str, description: str) -> Hotel:
        if not name.strip():
            raise ValidationError("Назва готелю не може бути порожньою.")
        if not city.strip():
            raise ValidationError("Місто не може бути порожнім.")
        if not address.strip():
            raise ValidationError("Адреса не може бути порожньою.")

        new_id = self._generate_id()
        hotel = Hotel(
            id=new_id,
            name=name.strip(),
            city=city.strip(),
            address=address.strip(),
            description=description.strip(),
        )

        items = self._get_all()
        items.append(hotel)
        self._save_all(items)
        return hotel

    def delete_hotel(self, hotel_id: int) -> None:
        items = self._get_all()
        new_items = [h for h in items if h.id != hotel_id]
        if len(new_items) == len(items):
            raise NotFoundError(f"Готель з ID {hotel_id} не знайдено.")
        self._save_all(new_items)

    def get_hotel(self, hotel_id: int) -> Hotel:
        return self._find_by_id_or_raise(hotel_id, f"Готель з ID {hotel_id} не знайдено.")

    def get_all_hotels(self) -> List[Hotel]:
        return self._get_all()

    def search_hotels(self, keyword: str) -> List[Hotel]:
       
        key = keyword.strip().lower()
        if not key:
            return self._get_all()

        result: List[Hotel] = []
        for h in self._get_all():
            text = f"{h.name} {h.city} {h.address} {h.description}".lower()
            if key in text:
                result.append(h)
        return result


class ClientService(BaseService[Client]):
    

    def add_client(self, first_name: str, last_name: str, phone: str, email: str) -> Client:
        first_name = first_name.strip()
        last_name = last_name.strip()
        if not first_name:
            raise ValidationError("Ім'я клієнта не може бути порожнім.")
        if not last_name:
            raise ValidationError("Прізвище клієнта не може бути порожнім.")

        new_id = self._generate_id()
        client = Client(
            id=new_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone.strip(),
            email=email.strip(),
        )

        items = self._get_all()
        items.append(client)
        self._save_all(items)
        return client

    def delete_client(self, client_id: int) -> None:
        items = self._get_all()
        new_items = [c for c in items if c.id != client_id]
        if len(new_items) == len(items):
            raise NotFoundError(f"Клієнта з ID {client_id} не знайдено.")
        self._save_all(new_items)

    def update_client(
        self,
        client_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Client:
        client = self._find_by_id_or_raise(client_id, f"Клієнта з ID {client_id} не знайдено.")

        if first_name is not None:
            first_name = first_name.strip()
            if not first_name:
                raise ValidationError("Ім'я клієнта не може бути порожнім.")
            client.first_name = first_name

        if last_name is not None:
            last_name = last_name.strip()
            if not last_name:
                raise ValidationError("Прізвище клієнта не може бути порожнім.")
            client.last_name = last_name

        if phone is not None:
            client.phone = phone.strip()

        if email is not None:
            client.email = email.strip()

        items = self._get_all()
        for i, c in enumerate(items):
            if c.id == client.id:
                items[i] = client
                break
        self._save_all(items)
        return client

    def get_client(self, client_id: int) -> Client:
        return self._find_by_id_or_raise(client_id, f"Клієнта з ID {client_id} не знайдено.")

    def get_all_clients(self) -> List[Client]:
        return self._get_all()

    def sort_clients_by_first_name(self) -> List[Client]:
        items = sorted(self._get_all(), key=lambda c: c.first_name.lower())
        # зберігаємо відсортований список як поточний стан
        self._save_all(items)
        return items

    def sort_clients_by_last_name(self) -> List[Client]:
        items = sorted(self._get_all(), key=lambda c: c.last_name.lower())
        self._save_all(items)
        return items

    def search_clients(self, keyword: str) -> List[Client]:
        key = keyword.strip().lower()
        if not key:
            return self._get_all()

        result: List[Client] = []
        for c in self._get_all():
            text = f"{c.first_name} {c.last_name} {c.phone} {c.email}".lower()
            if key in text:
                result.append(c)
        return result


class BookingService(BaseService[Booking]):
    

    def __init__(
        self,
        booking_repo: IRepository[Booking],
        hotel_repo: IRepository[Hotel],
        room_repo: IRepository[Room],
        client_repo: IRepository[Client],
    ):
        super().__init__(booking_repo)
        self._hotel_repo = hotel_repo
        self._room_repo = room_repo
        self._client_repo = client_repo

    # ===== Допоміжні методи =====

    def _validate_dates(self, check_in: date, check_out: date) -> None:
        if check_in >= check_out:
            raise ValidationError("Дата виїзду має бути пізніше за дату заїзду.")

    def _ensure_hotel_exists(self, hotel_id: int) -> Hotel:
        hotel = self._hotel_repo.get_by_id(hotel_id)
        if hotel is None:
            raise NotFoundError(f"Готель з ID {hotel_id} не знайдено.")
        return hotel

    def _ensure_room_exists(self, room_id: int) -> Room:
        room = self._room_repo.get_by_id(room_id)
        if room is None:
            raise NotFoundError(f"Кімнату з ID {room_id} не знайдено.")
        return room

    def _ensure_client_exists(self, client_id: int) -> Client:
        client = self._client_repo.get_by_id(client_id)
        if client is None:
            raise NotFoundError(f"Клієнта з ID {client_id} не знайдено.")
        return client

    def _filter_bookings_by_period(
        self,
        bookings: List[Booking],
        start_date: date,
        end_date: date,
    ) -> List[Booking]:
        """
        Повертає бронювання, що перетинаються із вказаним періодом.
        """
        result: List[Booking] = []
        for b in bookings:
            # Перетин періодів: [check_in, check_out) з [start_date, end_date)
            if b.check_in < end_date and b.check_out > start_date:
                result.append(b)
        return result

    # ===== 1.5. Додавання заявки =====

    def add_request(
        self,
        hotel_id: int,
        room_id: int,
        client_id: int,
        check_in: date,
        check_out: date,
        text: str = "",
    ) -> Booking:
        self._validate_dates(check_in, check_out)
        hotel = self._ensure_hotel_exists(hotel_id)
        room = self._ensure_room_exists(room_id)
        client = self._ensure_client_exists(client_id)

        # перевірка, що room.hotel_id == hotel.id
        if room.hotel_id != hotel.id:
            raise ValidationError("Кімната не належить вказаному готелю.")

        new_id = self._generate_id()
        booking = Booking(
            id=new_id,
            hotel_id=hotel.id,
            room_id=room.id,
            client_id=client.id,
            check_in=check_in,
            check_out=check_out,
            status=BookingStatus.PENDING,
            request_text=text.strip(),
        )

        items = self._get_all()
        items.append(booking)
        self._save_all(items)
        return booking

    # ===== 1.6. Видалення заявки =====

    def delete_request(self, booking_id: int) -> None:
        items = self._get_all()
        new_items = [b for b in items if b.id != booking_id]
        if len(new_items) == len(items):
            raise NotFoundError(f"Заявку / бронювання з ID {booking_id} не знайдено.")
        self._save_all(new_items)

    # ===== 1.7. Зміна тексту заявки =====

    def update_request_text(self, booking_id: int, new_text: str) -> Booking:
        booking = self._find_by_id_or_raise(
            booking_id,
            f"Заявку / бронювання з ID {booking_id} не знайдено.",
        )
        booking.request_text = new_text.strip()

        items = self._get_all()
        for i, b in enumerate(items):
            if b.id == booking.id:
                items[i] = booking
                break
        self._save_all(items)
        return booking

    # ===== 1.8. Перегляд заявок за період =====

    def get_requests_in_period(
        self,
        hotel_id: int,
        start_date: date,
        end_date: date,
    ) -> List[Booking]:
        self._ensure_hotel_exists(hotel_id)
        all_bookings = self._get_all()
        # Беремо тільки заявки зі статусом PENDING для цього готелю
        pending = [
            b for b in all_bookings
            if b.hotel_id == hotel_id and b.status == BookingStatus.PENDING
        ]
        return self._filter_bookings_by_period(pending, start_date, end_date)

    # ===== 3.1. Замовити номер (підтвердити заявку) =====

    def confirm_booking(self, booking_id: int) -> Booking:
        booking = self._find_by_id_or_raise(
            booking_id,
            f"Заявку / бронювання з ID {booking_id} не знайдено.",
        )
        if booking.status == BookingStatus.CANCELLED:
            raise ValidationError("Неможливо підтвердити скасоване бронювання.")
        booking.status = BookingStatus.CONFIRMED

        items = self._get_all()
        for i, b in enumerate(items):
            if b.id == booking.id:
                items[i] = booking
                break
        self._save_all(items)
        return booking

    # ===== 3.2. Відмінити замовлення =====

    def cancel_booking(self, booking_id: int) -> Booking:
        booking = self._find_by_id_or_raise(
            booking_id,
            f"Заявку / бронювання з ID {booking_id} не знайдено.",
        )
        booking.status = BookingStatus.CANCELLED

        items = self._get_all()
        for i, b in enumerate(items):
            if b.id == booking.id:
                items[i] = booking
                break
        self._save_all(items)
        return booking

    # ===== 3.3. Переглянути дані конкретного замовлення =====

    def get_booking(self, booking_id: int) -> Booking:
        return self._find_by_id_or_raise(
            booking_id,
            f"Заявку / бронювання з ID {booking_id} не знайдено.",
        )

    # ===== 3.4. Кількість заброньованих місць =====

    def get_reserved_places(
        self,
        hotel_id: int,
        start_date: date,
        end_date: date,
    ) -> Tuple[int, List[Room]]:
        """
        Повертає:
        - загальну кількість місць, заброньованих у готелі на період
        - список кімнат, які заброньовані
        """
        self._ensure_hotel_exists(hotel_id)

        all_bookings = self._get_all()
        confirmed = [
            b for b in all_bookings
            if b.hotel_id == hotel_id and b.status == BookingStatus.CONFIRMED
        ]
        confirmed_in_period = self._filter_bookings_by_period(
            confirmed, start_date, end_date
        )

        reserved_rooms: List[Room] = []
        total_places = 0
        seen_room_ids: Set[int] = set()

        for b in confirmed_in_period:
            room = self._ensure_room_exists(b.room_id)
            total_places += room.capacity
            if room.id not in seen_room_ids:
                reserved_rooms.append(room)
                seen_room_ids.add(room.id)

        return total_places, reserved_rooms

    # ===== 3.5. Кількість вільних місць =====

    def get_free_places(
        self,
        hotel_id: int,
        start_date: date,
        end_date: date,
    ) -> Tuple[int, List[Room]]:
        """
        Повертає:
        - загальну кількість вільних місць
        - список кімнат, які вільні в даний період
        """
        self._ensure_hotel_exists(hotel_id)

        # всі кімнати готелю
        all_rooms = [
            r for r in self._room_repo.get_all()
            if r.hotel_id == hotel_id
        ]

        # вже заброньовані кімнати у періоді
        _, reserved_rooms = self.get_reserved_places(hotel_id, start_date, end_date)
        reserved_ids = {r.id for r in reserved_rooms}

        free_rooms = [r for r in all_rooms if r.id not in reserved_ids]
        total_free_places = sum(r.capacity for r in free_rooms)

        return total_free_places, free_rooms

    # ===== 3.6. Вартість послуг замовлення =====

    def calculate_booking_price(self, booking_id: int) -> float:
        booking = self.get_booking(booking_id)
        room = self._ensure_room_exists(booking.room_id)
        days = booking.duration_days()
        if days <= 0:
            raise ValidationError("Неможливо порахувати вартість: тривалість проживання некоректна.")
        return room.price_per_night * days

    # ===== 3.7. Клієнти, які забронювали номери =====

    
    def get_clients_with_bookings(self, hotel_id: int) -> List[Client]:
        self._ensure_hotel_exists(hotel_id)
        bookings = [
            b for b in self._get_all()
            if b.hotel_id == hotel_id and b.status == BookingStatus.CONFIRMED
        ]
        client_ids: Set[int] = {b.client_id for b in bookings}

        result: List[Client] = []
        for cid in client_ids:
            client = self._client_repo.get_by_id(cid)
            if client is not None:
                result.append(client)
        return result