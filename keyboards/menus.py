"""Сборка клавиатур бота (JSON-клавиатуры ВКонтакте).

Каждая кнопка несет payload с командой, по которому бот однозначно
определяет действие пользователя. Кнопки-ссылки (openlink) открывают
страницы сайта, карты и сообщения сообщества.
"""

from __future__ import annotations

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from data.assortment import Category, get_button_label as get_category_label
from data.doctor import COMMUNITY_MESSAGES_URL, DOCTOR
from data.salons import Salon
from data.services import Service, get_button_label

# Команды, передаваемые в payload кнопок
CMD_START = "start"
CMD_SERVICES = "services"
CMD_SERVICE = "service"
CMD_ASSORTMENT = "assortment"
CMD_CATEGORY = "category"
CMD_SALONS = "salons"
CMD_DOCTOR = "doctor"
CMD_BOOK = "book"
CMD_ABOUT = "about"

MAX_BUTTON_LABEL = 40  # ограничение ВКонтакте на длину подписи кнопки


def main_menu_keyboard() -> VkKeyboard:
    """Собирает главное меню бота.

    Вид::

        Услуги | Ассортимент
        Салоны и адреса | Врач-ортопед
        О центре

    :return: клавиатура главного меню.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button("Услуги", color=VkKeyboardColor.PRIMARY, payload={"cmd": CMD_SERVICES})
    keyboard.add_button("Ассортимент", color=VkKeyboardColor.PRIMARY, payload={"cmd": CMD_ASSORTMENT})
    keyboard.add_line()
    keyboard.add_button("Салоны и адреса", payload={"cmd": CMD_SALONS})
    keyboard.add_button(
        "Врач-ортопед", color=VkKeyboardColor.POSITIVE, payload={"cmd": CMD_DOCTOR}
    )
    keyboard.add_line()
    keyboard.add_button("О центре", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_ABOUT})

    return keyboard


def services_keyboard(services: list[Service]) -> VkKeyboard:
    """Собирает клавиатуру списка услуг: каждая услуга — отдельная кнопка.

    Услуги располагаются по две в ряд, внизу — кнопка возврата
    в главное меню.

    :param services: список услуг для отображения;
    :return: клавиатура списка услуг.
    """
    keyboard = VkKeyboard(one_time=False)

    for index, service in enumerate(services):
        if index and index % 2 == 0:
            keyboard.add_line()
        keyboard.add_button(
            get_button_label(service),
            payload={"cmd": CMD_SERVICE, "id": service["id"]},
        )

    keyboard.add_line()
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})

    return keyboard


def service_card_keyboard(service_id: str) -> VkKeyboard:
    """Собирает клавиатуру карточки услуги.

    :param service_id: идентификатор текущей услуги;
    :return: клавиатура карточки услуги.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button(
        "Записаться к врачу", color=VkKeyboardColor.POSITIVE, payload={"cmd": CMD_BOOK}
    )
    keyboard.add_line()
    keyboard.add_button("Все услуги", payload={"cmd": CMD_SERVICES})
    keyboard.add_button("Главное меню", payload={"cmd": CMD_START})

    return keyboard


def assortment_keyboard(categories: list[Category]) -> VkKeyboard:
    """Собирает клавиатуру ассортимента: кнопка на каждый товарный раздел.

    :param categories: список товарных разделов;
    :return: клавиатура ассортимента.
    """
    keyboard = VkKeyboard(one_time=False)

    for index, category in enumerate(categories):
        if index and index % 2 == 0:
            keyboard.add_line()
        keyboard.add_button(
            get_category_label(category),
            payload={"cmd": CMD_CATEGORY, "id": category["id"]},
        )

    keyboard.add_line()
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})

    return keyboard


def category_card_keyboard(category_id: str) -> VkKeyboard:
    """Собирает клавиатуру карточки товарного раздела.

    :param category_id: идентификатор текущего раздела;
    :return: клавиатура карточки раздела.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button("Все разделы", payload={"cmd": CMD_ASSORTMENT})
    keyboard.add_button("Салоны и адреса", payload={"cmd": CMD_SALONS})
    keyboard.add_line()
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})

    return keyboard


def _map_label(salon: Salon) -> str:
    """Формирует короткую подпись кнопки-ссылки на карточку салона.

    :param salon: карточка точки продаж;
    :return: подпись не длиннее 40 символов.
    """
    street = salon["address"].split(", ")[0]
    label = f"Карта: {street}"
    return label[:MAX_BUTTON_LABEL]


def salons_keyboard(salons: list[Salon]) -> VkKeyboard:
    """Собирает клавиатуру раздела «Салоны и адреса».

    На каждую точку — кнопка-ссылка на Яндекс.Карты (дубли адресов
    схлопываются), внизу — возврат в главное меню.

    :param salons: список точек продаж;
    :return: клавиатура раздела салонов.
    """
    keyboard = VkKeyboard(one_time=False)
    seen: set[str] = set()
    first = True

    for salon in salons:
        if salon["map_url"] in seen:
            continue
        seen.add(salon["map_url"])
        if not first:
            keyboard.add_line()
        keyboard.add_openlink_button(_map_label(salon), salon["map_url"])
        first = False

    keyboard.add_line()
    keyboard.add_button(
        "Врач-ортопед", color=VkKeyboardColor.POSITIVE, payload={"cmd": CMD_DOCTOR}
    )
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})

    return keyboard


def doctor_keyboard() -> VkKeyboard:
    """Собирает клавиатуру раздела «Врач-ортопед».

    :return: клавиатура карточки врача.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button(
        "Записаться на приём", color=VkKeyboardColor.POSITIVE, payload={"cmd": CMD_BOOK}
    )
    keyboard.add_line()
    keyboard.add_openlink_button("Страница врача на сайте", DOCTOR["site_url"])
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})

    return keyboard


def booking_keyboard() -> VkKeyboard:
    """Собирает клавиатуру раздела «Запись к врачу».

    Кнопки-ссылки ведут в сообщения сообщества и на страницу врача.

    :return: клавиатура записи к врачу.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_openlink_button("Написать в сообщения", COMMUNITY_MESSAGES_URL)
    keyboard.add_line()
    keyboard.add_openlink_button("Страница врача", DOCTOR["site_url"])
    keyboard.add_line()
    keyboard.add_button("Назад к врачу", payload={"cmd": CMD_DOCTOR})
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})

    return keyboard


def back_to_main_keyboard() -> VkKeyboard:
    """Собирает клавиатуру с одной кнопкой возврата в главное меню.

    :return: клавиатура с кнопкой «Главное меню».
    """
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})
    return keyboard
