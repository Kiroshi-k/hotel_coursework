import unittest
from datetime import date

from bll.models import Hotel, Room, Client, Booking, BookingStatus
from bll.services import BookingService
from bll.exceptions import ValidationError, NotFoundError
from .in_memory_repository import InMemoryRepository


class BookingServiceTests(unittest.TestCase):
    """
    Базові тести для BookingService.
    Покриваємо основні сценарії:
    - створення заявки
    - помилкові дати
    - підтвердження / скасування
    - розрахунок вартості
    - вибірки по періоду, місця, клієнти
    """

    def setUp(self):
        # Arrange: створюємо in-memory репозиторії з базовими даними
        self.hotel_repo = InMemoryRepository[Hotel]([
            Hotel(id=1, name="Test Hotel", city="Київ",
                  address="Адреса 1", description="Опис"),
        ])

        self.room_repo = InMemoryRepository[Room]([
            Room(id=1, hotel_id=1, number="101", capacity=2, price_per_night=100.0),
            Room(id=2, hotel_id=1, number="102", capacity=3, price_per_night=150.0),
        ])

        self.client_repo = InMemoryRepository[Client]([
            Client(id=1, first_name="Іван", last_name="Клієнт",
                   phone="111", email="ivan@example.com"),
            Client(id=2, first_name="Петро", last_name="Клієнт",
                   phone="222", email="petro@example.com"),
        ])

        self.booking_repo = InMemoryRepository[Booking]([])

        self.service = BookingService(
            booking_repo=self.booking_repo,
            hotel_repo=self.hotel_repo,
            room_repo=self.room_repo,
            client_repo=self.client_repo,
        )

    def test_add_request_creates_pending_booking(self):
        # Arrange
        check_in = date(2025, 1, 1)
        check_out = date(2025, 1, 3)

        # Act
        booking = self.service.add_request(
            hotel_id=1,
            room_id=1,
            client_id=1,
            check_in=check_in,
            check_out=check_out,
            text="Тестова заявка",
        )

        # Assert
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.hotel_id, 1)
        self.assertEqual(len(self.booking_repo.get_all()), 1)

    def test_add_request_raises_for_invalid_dates(self):
        # Arrange
        check_in = date(2025, 1, 5)
        check_out = date(2025, 1, 1)

        # Act + Assert
        with self.assertRaises(ValidationError):
            self.service.add_request(
                hotel_id=1,
                room_id=1,
                client_id=1,
                check_in=check_in,
                check_out=check_out,
                text="",
            )

    def test_confirm_and_cancel_booking_change_status(self):
        # Arrange
        booking = self.service.add_request(
            hotel_id=1,
            room_id=1,
            client_id=1,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 2),
            text="",
        )

        # Act
        confirmed = self.service.confirm_booking(booking.id)
        cancelled = self.service.cancel_booking(booking.id)

        # Assert
        self.assertEqual(confirmed.status, BookingStatus.CONFIRMED)
        self.assertEqual(cancelled.status, BookingStatus.CANCELLED)

    def test_confirm_cancel_unknown_booking_raises_not_found(self):
        # Arrange / Act / Assert
        with self.assertRaises(NotFoundError):
            self.service.confirm_booking(999)

        with self.assertRaises(NotFoundError):
            self.service.cancel_booking(999)

    def test_calculate_booking_price_returns_correct_value(self):
        # Arrange
        booking = self.service.add_request(
            hotel_id=1,
            room_id=1,  # ціна за добу = 100
            client_id=1,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 4),  # 3 доби
            text="",
        )

        # Act
        price = self.service.calculate_booking_price(booking.id)

        # Assert
        self.assertEqual(price, 300.0)

    def test_get_requests_in_period_returns_only_pending_and_in_period(self):
        # Arrange
        # pending заявка в періоді
        b1 = self.service.add_request(
            hotel_id=1,
            room_id=1,
            client_id=1,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 5),
            text="",
        )
        # ще одна заявка, але поза періодом
        b2 = self.service.add_request(
            hotel_id=1,
            room_id=1,
            client_id=1,
            check_in=date(2025, 2, 1),
            check_out=date(2025, 2, 3),
            text="",
        )
        # цю заявку підтверджуємо – вона вже не PENDING
        self.service.confirm_booking(b2.id)

        # Act
        requests = self.service.get_requests_in_period(
            hotel_id=1,
            start_date=date(2024, 12, 31),
            end_date=date(2025, 1, 10),
        )

        # Assert
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].id, b1.id)
        self.assertEqual(requests[0].status, BookingStatus.PENDING)

    def test_get_reserved_and_free_places(self):
        # Arrange
        # бронюємо кімнату 1 (capacity=2) у періоді
        b = self.service.add_request(
            hotel_id=1,
            room_id=1,
            client_id=1,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 3),
            text="",
        )
        self.service.confirm_booking(b.id)

        # Act
        reserved_places, reserved_rooms = self.service.get_reserved_places(
            hotel_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10),
        )
        free_places, free_rooms = self.service.get_free_places(
            hotel_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10),
        )

        # Assert
        self.assertEqual(reserved_places, 2)  # кімната 101 з capacity=2
        self.assertEqual(len(reserved_rooms), 1)
        self.assertEqual(reserved_rooms[0].number, "101")

        # вільна залишається кімната 102 (capacity=3)
        self.assertEqual(free_places, 3)
        self.assertEqual(len(free_rooms), 1)
        self.assertEqual(free_rooms[0].number, "102")

    def test_get_clients_with_bookings_returns_only_confirmed_clients(self):
        # Arrange
        # заявка 1 – підтверджена
        b1 = self.service.add_request(
            hotel_id=1,
            room_id=1,
            client_id=1,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 2),
            text="",
        )
        self.service.confirm_booking(b1.id)

        # заявка 2 – лише pending
        self.service.add_request(
            hotel_id=1,
            room_id=2,
            client_id=2,
            check_in=date(2025, 1, 3),
            check_out=date(2025, 1, 4),
            text="",
        )

        # Act
        clients = self.service.get_clients_with_bookings(hotel_id=1)

        # Assert
        ids = {c.id for c in clients}
        self.assertIn(1, ids)
        self.assertNotIn(2, ids)  # клієнт 2 має тільки PENDING, не CONFIRMED


if __name__ == "__main__":
    unittest.main()
