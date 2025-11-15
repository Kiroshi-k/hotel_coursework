from __future__ import annotations

from typing import TypeVar, Generic, Callable, List, Optional

from bll.services import IRepository
from .file_storage import FileStorage

T = TypeVar("T")


class JsonRepository(IRepository[T], Generic[T]):
    """
    Універсальний репозиторій для зберігання об'єктів у JSON-файлах.

    Працює через:
    - FileStorage (читає/пише список dict'ів)
    - factory: dict -> об'єкт (T)
    - to_dict: об'єкт (T) -> dict

    Так ми маємо:
    - інкапсуляцію роботи з файлами у DAL
    - поліморфізм (JsonRepository[T] реалізує IRepository[T])
    """

    def __init__(
        self,
        storage: FileStorage,
        factory: Callable[[dict], T],
        to_dict: Callable[[T], dict],
    ):
        self._storage = storage
        self._factory = factory
        self._to_dict = to_dict

    def get_all(self) -> List[T]:
        raw_items = self._storage.load_all()
        return [self._factory(item) for item in raw_items]

    def get_by_id(self, id_: int) -> Optional[T]:
        # простий пошук по ID
        for item in self.get_all():
            if getattr(item, "id", None) == id_:
                return item
        return None

    def save_all(self, items: List[T]) -> None:
        raw_items = [self._to_dict(item) for item in items]
        self._storage.save_all(raw_items)
