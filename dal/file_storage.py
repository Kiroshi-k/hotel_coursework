from pathlib import Path
import json
from typing import List, Dict, Any


class FileStorage:
    """
    Примітивне сховище:
    - зберігає список dict'ів у JSON-файлі
    - завантажує список dict'ів з файлу
    """

    def __init__(self, file_path: str):
        self._path = Path(file_path)

    def load_all(self) -> List[Dict[str, Any]]:
        """
        Повертає список словників із файлу.
        Якщо файлу ще немає – повертає порожній список.
        """
        if not self._path.exists():
            return []

        with self._path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                # якщо в файлі щось інше – вважаємо, що даних немає
                return []
            except json.JSONDecodeError:
                # файл пошкоджений / порожній
                return []

    def save_all(self, items: List[Dict[str, Any]]) -> None:
        """
        Зберігає список словників у JSON-файлі.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
