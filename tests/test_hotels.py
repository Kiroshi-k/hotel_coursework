import unittest

from bll.models import Hotel
from bll.services import HotelService
from bll.exceptions import ValidationError, NotFoundError
from .in_memory_repository import InMemoryRepository


class HotelServiceTests(unittest.TestCase):
    

    def setUp(self):
        # Arrange
        initial_hotels = [
            Hotel(id=1, name="Kyiv Hotel", city="Київ",
                  address="Вул. Хрещатик, 1", description="Центральний готель"),
        ]
        self.repo = InMemoryRepository[Hotel](initial_hotels)
        self.service = HotelService(self.repo)

    def test_add_hotel_creates_new_hotel(self):
        # Arrange
        # Act
        hotel = self.service.add_hotel(
            name="Lviv Hotel",
            city="Львів",
            address="Площа Ринок, 1",
            description="Готель у Львові",
        )

        # Assert
        self.assertEqual(hotel.id, 2)
        self.assertEqual(hotel.city, "Львів")
        self.assertEqual(len(self.repo.get_all()), 2)

    def test_add_hotel_raises_validation_error_for_empty_name(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValidationError):
            self.service.add_hotel(
                name="   ",
                city="Київ",
                address="Адреса",
                description="Опис",
            )

    def test_delete_hotel_removes_hotel(self):
        # Arrange
        hotel_id = 1

        # Act
        self.service.delete_hotel(hotel_id)

        # Assert
        ids = [h.id for h in self.repo.get_all()]
        self.assertNotIn(hotel_id, ids)

    def test_delete_hotel_raises_not_found(self):
        # Arrange / Act / Assert
        with self.assertRaises(NotFoundError):
            self.service.delete_hotel(999)

    def test_search_hotels_finds_by_keyword(self):
        # Arrange
        keyword = "kyiv".lower()

        # Act
        results = self.service.search_hotels(keyword)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Kyiv Hotel")


if __name__ == "__main__":
    unittest.main()
