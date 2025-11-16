import unittest

from bll.models import Client
from bll.services import ClientService
from bll.exceptions import ValidationError, NotFoundError
from .in_memory_repository import InMemoryRepository


class ClientServiceTests(unittest.TestCase):
   

    def setUp(self):
        # Arrange: початкові дані
        initial_clients = [
            Client(id=1, first_name="Іван", last_name="Петренко",
                   phone="111", email="ivan@example.com"),
            Client(id=2, first_name="Петро", last_name="Іванов",
                   phone="222", email="petro@example.com"),
        ]
        self.repo = InMemoryRepository[Client](initial_clients)
        self.service = ClientService(self.repo)

    def test_add_client_creates_client_with_new_id(self):
        # Arrange
        first_name = "Анна"
        last_name = "Сидоренко"

        # Act
        client = self.service.add_client(first_name, last_name, "333", "anna@example.com")

        # Assert
        self.assertEqual(client.first_name, "Анна")
        self.assertEqual(client.last_name, "Сидоренко")
        self.assertEqual(client.id, 3)  # попередні мали id 1 і 2
        self.assertEqual(len(self.repo.get_all()), 3)

    def test_add_client_raises_validation_error_for_empty_first_name(self):
        # Arrange
        # порожнє ім'я
        # Act + Assert
        with self.assertRaises(ValidationError):
            self.service.add_client("", "Прізвище", "123", "a@b.c")

    def test_add_client_raises_validation_error_for_empty_last_name(self):
        # Arrange / Act / Assert
        with self.assertRaises(ValidationError):
            self.service.add_client("Ім'я", "   ", "123", "a@b.c")

    def test_delete_client_removes_client(self):
        # Arrange
        existing_id = 1

        # Act
        self.service.delete_client(existing_id)

        # Assert
        ids = [c.id for c in self.repo.get_all()]
        self.assertNotIn(existing_id, ids)

    def test_delete_client_raises_not_found_for_unknown_id(self):
        # Arrange
        unknown_id = 999

        # Act + Assert
        with self.assertRaises(NotFoundError):
            self.service.delete_client(unknown_id)

    def test_update_client_changes_fields(self):
        # Arrange
        client_id = 1

        # Act
        updated = self.service.update_client(
            client_id,
            first_name="Оновлене ім'я",
            last_name="Оновлене прізвище",
            phone="999",
            email="new@example.com",
        )

        # Assert
        self.assertEqual(updated.first_name, "Оновлене ім'я")
        self.assertEqual(updated.last_name, "Оновлене прізвище")
        self.assertEqual(updated.phone, "999")
        self.assertEqual(updated.email, "new@example.com")

    def test_update_client_raises_for_empty_first_name(self):
        # Arrange
        client_id = 1

        # Act + Assert
        with self.assertRaises(ValidationError):
            self.service.update_client(client_id, first_name="   ")

    def test_get_client_returns_correct_client(self):
        # Arrange
        client_id = 2

        # Act
        client = self.service.get_client(client_id)

        # Assert
        self.assertEqual(client.id, client_id)
        self.assertEqual(client.first_name, "Петро")

    def test_get_client_raises_not_found_for_unknown_id(self):
        # Arrange
        unknown_id = 999

        # Act + Assert
        with self.assertRaises(NotFoundError):
            self.service.get_client(unknown_id)

    def test_sort_clients_by_first_name_sorts_ascending(self):
        # Arrange
        # Act
        sorted_clients = self.service.sort_clients_by_first_name()

        # Assert
        first_names = [c.first_name for c in sorted_clients]
        self.assertEqual(first_names, sorted(first_names))

    def test_sort_clients_by_last_name_sorts_ascending(self):
        # Arrange
        # Act
        sorted_clients = self.service.sort_clients_by_last_name()

        # Assert
        last_names = [c.last_name for c in sorted_clients]
        self.assertEqual(last_names, sorted(last_names))

    def test_search_clients_finds_by_name_and_email(self):
        # Arrange
        keyword = "іван"  # знайде і Іван, і Іванов

        # Act
        results = self.service.search_clients(keyword)

        # Assert
        self.assertTrue(any("Іван" in c.first_name or "Іванов" in c.last_name for c in results))

        # Arrange (інший пошук – по email)
        keyword_email = "petro@example.com"

        # Act
        results_email = self.service.search_clients(keyword_email)

        # Assert
        self.assertEqual(len(results_email), 1)
        self.assertEqual(results_email[0].email, "petro@example.com")


if __name__ == "__main__":
    unittest.main()
