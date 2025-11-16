import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from datetime import date
import pandas as pd
from dal import FileStorage, JsonRepository
from bll.models import Hotel, Room, Client, Booking, BookingStatus
from bll.services import HotelService, ClientService, BookingService
from bll.exceptions import ValidationError, NotFoundError


# ===================== ІНІЦІАЛІЗАЦІЯ СЕРВІСІВ =====================

@st.cache_resource
def get_services():
    # Репозиторії
    hotel_repo = JsonRepository[Hotel](
        storage=FileStorage("data/hotels.json"),
        factory=lambda d: Hotel(
            id=d["id"],
            name=d["name"],
            city=d["city"],
            address=d["address"],
            description=d.get("description", ""),
        ),
        to_dict=lambda h: {
            "id": h.id,
            "name": h.name,
            "city": h.city,
            "address": h.address,
            "description": h.description,
        },
    )

    room_repo = JsonRepository[Room](
        storage=FileStorage("data/rooms.json"),
        factory=lambda d: Room(
            id=d["id"],
            hotel_id=d["hotel_id"],
            number=d["number"],
            capacity=d["capacity"],
            price_per_night=d["price_per_night"],
        ),
        to_dict=lambda r: {
            "id": r.id,
            "hotel_id": r.hotel_id,
            "number": r.number,
            "capacity": r.capacity,
            "price_per_night": r.price_per_night,
        },
    )

    client_repo = JsonRepository[Client](
        storage=FileStorage("data/clients.json"),
        factory=lambda d: Client(
            id=d["id"],
            first_name=d["first_name"],
            last_name=d["last_name"],
            phone=d.get("phone", ""),
            email=d.get("email", ""),
        ),
        to_dict=lambda c: {
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "phone": c.phone,
            "email": c.email,
        },
    )

    booking_repo = JsonRepository[Booking](
        storage=FileStorage("data/bookings.json"),
        factory=lambda d: Booking(
            id=d["id"],
            hotel_id=d["hotel_id"],
            room_id=d["room_id"],
            client_id=d["client_id"],
            check_in=date.fromisoformat(d["check_in"]),
            check_out=date.fromisoformat(d["check_out"]),
            status=BookingStatus(d["status"]),
            request_text=d.get("request_text", ""),
        ),
        to_dict=lambda b: {
            "id": b.id,
            "hotel_id": b.hotel_id,
            "room_id": b.room_id,
            "client_id": b.client_id,
            "check_in": b.check_in.isoformat(),
            "check_out": b.check_out.isoformat(),
            "status": b.status.value,
            "request_text": b.request_text,
        },
    )

    # Сервіси
    hotel_service = HotelService(hotel_repo)
    client_service = ClientService(client_repo)
    booking_service = BookingService(
        booking_repo=booking_repo,
        hotel_repo=hotel_repo,
        room_repo=room_repo,
        client_repo=client_repo,
    )

    return hotel_service, client_service, booking_service, room_repo


hotel_service, client_service, booking_service, room_repo = get_services()


# ========================== ДОПОМІЖНІ =============================

def show_error(e: Exception):
    st.error(str(e))


def get_hotels_for_select():
    hotels = hotel_service.get_all_hotels()
    return {f"{h.name} ({h.city}) [ID={h.id}]" : h for h in hotels}


def get_clients_for_select():
    clients = client_service.get_all_clients()
    return {f"{c.first_name} {c.last_name} [ID={c.id}]" : c for c in clients}


def get_rooms_for_hotel(hotel_id: int):
    rooms = [r for r in room_repo.get_all() if r.hotel_id == hotel_id]
    return rooms


# ======================= СТОРІНКА: ГОТЕЛІ =========================

def page_hotels():
    st.header("Управління готелями")

    col1, col2 = st.columns(2)

    # ----- Додати готель -----
    with col1:
        st.subheader("Додати готель")

        name = st.text_input("Назва готелю")
        city = st.text_input("Місто")
        address = st.text_input("Адреса")
        description = st.text_area("Опис")

        if st.button("Зберегти готель"):
            try:
                hotel_service.add_hotel(name, city, address, description)
                st.success("Готель додано.")
                st.rerun()

            except (ValidationError, Exception) as e:
                show_error(e)

    # ----- Список готелів -----
    with col2:
        st.subheader("Список готелів")

        hotels = hotel_service.get_all_hotels()
        if not hotels:
            st.info("Ще немає жодного готелю.")
        else:
            df = pd.DataFrame([
                 {
                    "ID": h.id,
                    "Назва": h.name,
                    "Місто": h.city,
                    "Адреса": h.address,
                    "Опис": h.description,
               } for h in hotels
     
            ]) 
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Видалення
            hotel_map = {f"{h.name} ({h.city}) [ID={h.id}]": h for h in hotels}
            selected = st.selectbox(
                "Видалити готель",
                ["- оберіть -"] + list(hotel_map.keys()),
            )
            if selected != "- оберіть -":
                if st.button("Видалити обраний готель"):
                    try:
                        hotel_service.delete_hotel(hotel_map[selected].id)
                        st.success("Готель видалено.")
                        st.rerun()

                    except NotFoundError as e:
                        show_error(e)

    st.markdown("---")
    st.subheader("Кімнати в готелі")

    hotel_map = get_hotels_for_select()
    if not hotel_map:
        st.info("Спочатку додайте хоча б один готель, щоб працювати з кімнатами.")
        return

    hotel_key = st.selectbox("Оберіть готель", list(hotel_map.keys()))
    selected_hotel = hotel_map[hotel_key]

    col3, col4 = st.columns(2)

    with col3:
        st.caption(f"Кімнати готелю **{selected_hotel.name}**")

        rooms = get_rooms_for_hotel(selected_hotel.id)
        if rooms:
            st.table(
                [{
                    "ID": r.id,
                    "Номер": r.number,
                    "Місць": r.capacity,
                    "Ціна за добу": r.price_per_night,
                } for r in rooms]
            )
        else:
            st.info("Поки що в готелі немає жодної кімнати.")

    with col4:
        st.caption("Додати кімнату")

        number = st.text_input("Номер кімнати (наприклад 101)")
        capacity = st.number_input("Кількість місць", min_value=1, value=2, step=1)
        price = st.number_input("Ціна за добу", min_value=0.0, value=1000.0, step=100.0)

        if st.button("Додати кімнату"):
            try:
                # простий валідейшн на рівні PL
                if not number.strip():
                    st.warning("Введіть номер кімнати.")
                else:
                    # створюємо кімнату через room_repo напряму
                    # (можна було б мати окремий RoomService, але для КР вистачить так)
                    all_rooms = room_repo.get_all()
                    new_id = max([r.id for r in all_rooms], default=0) + 1
                    room = Room(
                        id=new_id,
                        hotel_id=selected_hotel.id,
                        number=number.strip(),
                        capacity=int(capacity),
                        price_per_night=float(price),
                    )
                    all_rooms.append(room)
                    room_repo.save_all(all_rooms)
                    st.success("Кімнату додано.")
                    st.rerun()
            except Exception as e:
                show_error(e)


# ======================= СТОРІНКА: КЛІЄНТИ ========================

def page_clients():
    st.header("Управління клієнтами")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Додати нового клієнта")

        first_name = st.text_input("Ім'я")
        last_name = st.text_input("Прізвище")
        phone = st.text_input("Телефон")
        email = st.text_input("Email")

        if st.button("Зберегти клієнта"):
            try:
                client_service.add_client(first_name, last_name, phone, email)
                st.success("Клієнта додано.")
                st.rerun()
            except ValidationError as e:
                show_error(e)

    with col2:
        st.subheader("Список клієнтів")

        clients = client_service.get_all_clients()
        if not clients:
            st.info("Поки що немає жодного клієнта.")
        else:
            st.table(
                [{
                    "ID": c.id,
                    "Ім'я": c.first_name,
                    "Прізвище": c.last_name,
                    "Телефон": c.phone,
                    "Email": c.email,
                } for c in clients]
            )

            st.markdown("**Сортування:**")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("За ім'ям"):
                    client_service.sort_clients_by_first_name()
                    st.rerun()
            with c2:
                if st.button("За прізвищем"):
                    client_service.sort_clients_by_last_name()
                    st.rerun()

    st.markdown("---")
    st.subheader("Редагування / видалення клієнта")

    client_map = get_clients_for_select()
    if not client_map:
        st.info("Немає клієнтів для редагування.")
        return

    key = st.selectbox("Оберіть клієнта", list(client_map.keys()))
    client = client_map[key]

    new_first_name = st.text_input("Нове ім'я", value=client.first_name)
    new_last_name = st.text_input("Нове прізвище", value=client.last_name)
    new_phone = st.text_input("Новий телефон", value=client.phone)
    new_email = st.text_input("Новий email", value=client.email)

    col3, col4 = st.columns(2)
    with col3:
        if st.button("Оновити дані клієнта"):
            try:
                client_service.update_client(
                    client.id,
                    first_name=new_first_name,
                    last_name=new_last_name,
                    phone=new_phone,
                    email=new_email,
                )
                st.success("Дані клієнта оновлено.")
                st.rerun()
            except ValidationError as e:
                show_error(e)

    with col4:
        if st.button("Видалити цього клієнта"):
            try:
                client_service.delete_client(client.id)
                st.success("Клієнта видалено.")
                st.rerun()
            except NotFoundError as e:
                show_error(e)


# ===================== СТОРІНКА: ЗАМОВЛЕННЯ =======================

def page_bookings():
    st.header("Замовлення номерів")

    hotel_map = get_hotels_for_select()
    if not hotel_map:
        st.info("Спочатку додайте готель і кімнати.")
        return

    hotel_key = st.selectbox("Оберіть готель", list(hotel_map.keys()))
    hotel = hotel_map[hotel_key]

    rooms = get_rooms_for_hotel(hotel.id)
    if not rooms:
        st.warning("У цього готелю немає кімнат. Додайте їх на сторінці 'Готелі'.")
        return

    clients_map = get_clients_for_select()
    if not clients_map:
        st.warning("Немає клієнтів. Додайте клієнта на сторінці 'Клієнти'.")
        return

    tab_new, tab_manage, tab_stats = st.tabs(
        ["Нова заявка", "Керування бронюваннями", "Статистика / період"]
    )

    # ----- НОВА ЗАЯВКА -----
    with tab_new:
        st.subheader("Створити нову заявку на бронювання")

        room_labels = {f"Кімната {r.number} (місць: {r.capacity}, ціна: {r.price_per_night})": r for r in rooms}
        room_key = st.selectbox("Кімната", list(room_labels.keys()))
        room = room_labels[room_key]

        client_key = st.selectbox("Клієнт", list(clients_map.keys()))
        client = clients_map[client_key]

        col_date1, col_date2 = st.columns(2)
        with col_date1:
            check_in = st.date_input("Дата заїзду", value=date.today())
        with col_date2:
            check_out = st.date_input("Дата виїзду", value=date.today())

        request_text = st.text_area("Текст заявки (побажання)", "")

        if st.button("Створити заявку"):
            try:
                booking_service.add_request(
                    hotel_id=hotel.id,
                    room_id=room.id,
                    client_id=client.id,
                    check_in=check_in,
                    check_out=check_out,
                    text=request_text,
                )
                st.success("Заявку створено.")
                st.rerun()
            except (ValidationError, NotFoundError) as e:
                show_error(e)

    # ----- КЕРУВАННЯ БРОНЮВАННЯМИ -----
    with tab_manage:
        st.subheader("Список заявок та бронювань для готелю")

        all_bookings = [
            b for b in booking_service._get_all()  # використали внутрішній метод, для спрощення
            if b.hotel_id == hotel.id
        ]
        if not all_bookings:
            st.info("Ще немає жодної заявки / бронювання для цього готелю.")
        else:
            st.table(
                [{
                    "ID": b.id,
                    "Кімната": b.room_id,
                    "Клієнт": b.client_id,
                    "Заїзд": b.check_in,
                    "Виїзд": b.check_out,
                    "Статус": b.status.value,
                    "Текст": b.request_text,
                } for b in all_bookings]
            )

            id_list = [b.id for b in all_bookings]
            selected_id = st.selectbox("ID замовлення для дій", id_list)

            action = st.radio(
                "Дія",
                ["Підтвердити бронювання", "Скасувати бронювання",
                 "Змінити текст заявки", "Видалити замовлення", "Порахувати вартість"],
            )

            if action == "Змінити текст заявки":
                new_text = st.text_area("Новий текст заявки", "")
            else:
                new_text = None

            if st.button("Виконати дію"):
                try:
                    if action == "Підтвердити бронювання":
                        booking_service.confirm_booking(selected_id)
                        st.success("Бронювання підтверджено.")
                    elif action == "Скасувати бронювання":
                        booking_service.cancel_booking(selected_id)
                        st.success("Бронювання скасовано.")
                    elif action == "Змінити текст заявки":
                        booking_service.update_request_text(selected_id, new_text or "")
                        st.success("Текст заявки змінено.")
                    elif action == "Видалити замовлення":
                        booking_service.delete_request(selected_id)
                        st.success("Замовлення видалено.")
                    elif action == "Порахувати вартість":
                        price = booking_service.calculate_booking_price(selected_id)
                        st.info(f"Вартість бронювання: {price:.2f}")
                    st.rerun()
                except (ValidationError, NotFoundError) as e:
                    show_error(e)

    # ----- СТАТИСТИКА / ПЕРІОД -----
    with tab_stats:
        st.subheader("Перегляд за періодом")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            start_date = st.date_input("Початок періоду", value=date.today())
        with col_p2:
            end_date = st.date_input("Кінець періоду", value=date.today())

        if st.button("Показати дані за період"):
            try:
                # заявки за період
                pending = booking_service.get_requests_in_period(
                    hotel_id=hotel.id,
                    start_date=start_date,
                    end_date=end_date,
                )
                st.markdown("**Заявки (PENDING) за період:**")
                if pending:
                    st.table(
                        [{
                            "ID": b.id,
                            "Кімната": b.room_id,
                            "Клієнт": b.client_id,
                            "Заїзд": b.check_in,
                            "Виїзд": b.check_out,
                            "Текст": b.request_text,
                        } for b in pending]
                    )
                else:
                    st.write("Немає заявок за вказаний період.")

                # заброньовані місця
                reserved_places, reserved_rooms = booking_service.get_reserved_places(
                    hotel_id=hotel.id,
                    start_date=start_date,
                    end_date=end_date,
                )
                st.markdown(f"**Кількість заброньованих місць:** {reserved_places}")
                if reserved_rooms:
                    st.table(
                        [{
                            "ID кімнати": r.id,
                            "Номер": r.number,
                            "Місць": r.capacity,
                            "Ціна за добу": r.price_per_night,
                        } for r in reserved_rooms]
                    )

                # вільні місця
                free_places, free_rooms = booking_service.get_free_places(
                    hotel_id=hotel.id,
                    start_date=start_date,
                    end_date=end_date,
                )
                st.markdown(f"**Кількість вільних місць:** {free_places}")
                if free_rooms:
                    st.table(
                        [{
                            "ID кімнати": r.id,
                            "Номер": r.number,
                            "Місць": r.capacity,
                            "Ціна за добу": r.price_per_night,
                        } for r in free_rooms]
                    )

                # клієнти з бронюваннями
                st.markdown("**Клієнти, які забронювали номери в готелі:**")
                clients = booking_service.get_clients_with_bookings(hotel.id)
                if clients:
                    st.table(
                        [{
                            "ID": c.id,
                            "Ім'я": c.first_name,
                            "Прізвище": c.last_name,
                            "Телефон": c.phone,
                            "Email": c.email,
                        } for c in clients]
                    )
                else:
                    st.write("Поки що немає клієнтів з активними бронюваннями.")
            except (ValidationError, NotFoundError) as e:
                show_error(e)


# ======================== СТОРІНКА: ПОШУК ========================

def page_search():
    st.header("Пошук")

    tab_hotel, tab_client = st.tabs(["Готелі", "Клієнти"])

    with tab_hotel:
        st.subheader("Пошук по готелях")
        keyword = st.text_input("Ключове слово (назва, місто, адреса, опис)", key="hotel_search")
        if st.button("Шукати готелі"):
           result = hotel_service.search_hotels(keyword)
           if result:
               df = pd.DataFrame(
                [
                {
                    "ID": h.id,
                    "Назва": h.name,
                    "Місто": h.city,
                    "Адреса": h.address,
                    "Опис": h.description,
                } for h in result]
               )
             st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                 st.info("Нічого не знайдено.")
 

    with tab_client:
        st.subheader("Пошук по клієнтах")
        keyword_c = st.text_input("Ключове слово (ім'я, прізвище, телефон, email)", key="client_search")
        if st.button("Шукати клієнтів"):
            result = client_service.search_clients(keyword_c)
            if result:
                st.table(
                    [{
                        "ID": c.id,
                        "Ім'я": c.first_name,
                        "Прізвище": c.last_name,
                        "Телефон": c.phone,
                        "Email": c.email,
                    } for c in result]
                )
            else:
                st.info("Нічого не знайдено.")


# ============================ ГОЛОВНА ============================

def main():
    st.set_page_config(page_title="Система бронювання готелю", layout="wide")
    st.title("Система бронювання номерів в готелі")

    page = st.sidebar.radio(
        "Меню",
        ["Готелі", "Клієнти", "Замовлення", "Пошук"],
    )

    if page == "Готелі":
        page_hotels()
    elif page == "Клієнти":
        page_clients()
    elif page == "Замовлення":
        page_bookings()
    elif page == "Пошук":
        page_search()


if __name__ == "__main__":
    main()
