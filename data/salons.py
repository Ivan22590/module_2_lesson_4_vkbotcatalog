"""Салоны и магазины ортоцентра «Авиценна»: адреса, телефоны, график.

Данные взяты со страницы «Адреса» и раздела «Ортопедические салоны»
сайта https://avicenna-vbg.ru/adress
"""

from __future__ import annotations

from typing import TypedDict


class Salon(TypedDict):
    """Точка продаж ортоцентра.

    :param id: уникальный идентификатор точки;
    :param name: название магазина или салона;
    :param city: город;
    :param address: улица и номер дома;
    :param phone: телефон для справок;
    :param hours: график работы (многострочный);
    :param map_url: ссылка на карточку организации в Яндекс.Картах.
    """

    id: str
    name: str
    city: str
    address: str
    phone: str
    hours: str
    map_url: str


_HOURS_MAIN = "пн-сб 10:00-19:00\nвс 10:00-18:00\nбез обеда"
_HOURS_KUYBYSHEVA = "пн-сб 10:00-19:00\nвс 10:00-17:00\nбез обеда"

SALONS: list[Salon] = [
    {
        "id": "kutuzova",
        "name": "Салон «Авиценна»",
        "city": "Выборг",
        "address": "бульвар Кутузова, д. 9",
        "phone": "8 (81378) 2-63-42",
        "hours": _HOURS_MAIN,
        "map_url": "https://yandex.ru/maps/org/avitsenna/39227017955/"
        "?ll=28.751188%2C60.705535&z=18",
    },
    {
        "id": "leningradskoe",
        "name": "Салон «Авиценна»",
        "city": "Выборг",
        "address": "Ленинградское шоссе, д. 57",
        "phone": "8 (993) 958-52-90",
        "hours": _HOURS_MAIN,
        "map_url": "https://yandex.ru/maps/org/avitsenna/1277927260/"
        "?ll=28.784140%2C60.699322&z=18",
    },
    {
        "id": "kuibysheva",
        "name": "Салон «Авиценна»",
        "city": "Выборг",
        "address": "ул. Куйбышева, д. 9",
        "phone": "8 (81378) 2-73-56",
        "hours": _HOURS_KUYBYSHEVA,
        "map_url": "https://yandex.ru/maps/org/avitsenna/1313877905/"
        "?ll=28.755854%2C60.711861&z=18",
    },
    {
        "id": "obuv_orto",
        "name": "Магазин «Обувь Орто»",
        "city": "Выборг",
        "address": "ул. Куйбышева, д. 9",
        "phone": "8 (81378) 2-73-56",
        "hours": _HOURS_KUYBYSHEVA,
        # Магазин находится по тому же адресу, что и салон на Куйбышева, 9
        "map_url": "https://yandex.ru/maps/org/avitsenna/1313877905/"
        "?ll=28.755854%2C60.711861&z=18",
    },
]


def build_salons_list() -> str:
    """Формирует сообщение со списком всех салонов и магазинов.

    :return: текст с адресами, телефонами и графиком работы.
    """
    lines = ["Салоны и магазины «Авиценна» — Выборг", ""]
    for index, salon in enumerate(SALONS, start=1):
        lines.append(f"{index}. {salon['name']}")
        lines.append(f"Адрес: {salon['city']}, {salon['address']}")
        lines.append(f"Телефон: {salon['phone']}")
        lines.append("График работы:")
        lines.extend(f"   {row}" for row in salon["hours"].split("\n"))
        lines.append("")
    lines.append("Кнопки ниже открывают адрес на Яндекс.Картах.")
    return "\n".join(lines)


def get_salon(salon_id: str) -> Salon | None:
    """Возвращает салон по его идентификатору.

    :param salon_id: идентификатор точки, например ``kutuzova``;
    :return: карточка салона или None, если точка не найдена.
    """
    for salon in SALONS:
        if salon["id"] == salon_id:
            return salon
    return None
