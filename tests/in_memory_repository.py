from typing import Generic, TypeVar, List, Optional

from bll.services import IRepository

T = TypeVar("T")


class InMemoryRepository(IRepository[T], Generic[T]):
    

    def __init__(self, initial: Optional[List[T]] = None):
        self._items: List[T] = list(initial) if initial is not None else []

    def get_all(self) -> List[T]:
        # повертаємо копію, щоб зовні не ламали внутрішній список
        return list(self._items)

    def get_by_id(self, id_: int) -> Optional[T]:
        for item in self._items:
            if getattr(item, "id", None) == id_:
                return item
        return None

    def save_all(self, items: List[T]) -> None:
        # зберігаємо копію, щоб уникнути побічних ефектів
        self._items = list(items)
