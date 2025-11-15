class ValidationError(Exception):
    """
    Помилка валідації бізнес-даних.
    Наприклад:
    - capacity <= 0;
    - price_per_night <= 0;
    - check_in >= check_out;
    - порожнє ім'я / прізвище тощо.
    """
    pass


class NotFoundError(Exception):
    """
    Об'єкт не знайдено (готель, клієнт, кімната, бронювання).
    Використовуватиметься в сервісах BLL.
    """
    pass
