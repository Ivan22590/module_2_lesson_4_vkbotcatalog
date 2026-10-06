"""Сборка клавиатур бота (JSON-клавиатуры ВКонтакте).

Каждая кнопка несет payload с командой, по которому бот однозначно
определяет действие пользователя.
"""

from __future__ import annotations

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from data.services import MANAGER, Service, get_button_label

# Команды, передаваемые в payload кнопок
CMD_START = "start"
CMD_CATALOG = "catalog"
CMD_PRICE = "price"
CMD_MANAGER = "manager"
CMD_ABOUT = "about"
CMD_SERVICE = "service"

MAX_BUTTON_LABEL = 40  # ограничение ВКонтакте на длину подписи кнопки


def main_menu_keyboard() -> VkKeyboard:
    """Собирает главное меню бота.

    Вид::

        Каталог услуг | Прайс-лист
        Связаться с менеджером | О салоне

    :return: клавиатура главного меню.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button("Каталог услуг", color=VkKeyboardColor.PRIMARY, payload={"cmd": CMD_CATALOG})
    keyboard.add_button("Прайс-лист", color=VkKeyboardColor.PRIMARY, payload={"cmd": CMD_PRICE})
    keyboard.add_line()
    keyboard.add_button(
        "Связаться с менеджером", color=VkKeyboardColor.POSITIVE, payload={"cmd": CMD_MANAGER}
    )
    keyboard.add_button("О салоне", payload={"cmd": CMD_ABOUT})

    return keyboard


def catalog_keyboard(services: list[Service]) -> VkKeyboard:
    """Собирает клавиатуру каталога: каждая услуга — отдельная кнопка.

    Услуги располагаются по две в ряд, внизу — кнопка возврата
    в главное меню.

    :param services: список услуг для отображения;
    :return: клавиатура каталога.
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

    :param id: идентификатор текущей услуги;
    :return: клавиатура карточки услуги.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button("Назад в каталог", payload={"cmd": CMD_CATALOG})
    keyboard.add_button("Главное меню", payload={"cmd": CMD_START})
    keyboard.add_line()
    keyboard.add_button(
        "Связаться с менеджером",
        color=VkKeyboardColor.POSITIVE,
        payload={"cmd": CMD_MANAGER},
    )

    return keyboard


def manager_keyboard() -> VkKeyboard:
    """Собирает клавиатуру раздела «Связаться с менеджером».

    Включает кнопку-ссылку на сообщения сообщества и возврат в меню.

    :return: клавиатура контактов менеджера.
    """
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_openlink_button("Написать менеджеру", MANAGER["messages_url"])
    keyboard.add_line()
    keyboard.add_button("Главное меню", payload={"cmd": CMD_START})

    return keyboard


def back_to_main_keyboard() -> VkKeyboard:
    """Собирает клавиатуру с одной кнопкой возврата в главное меню.

    :return: клавиатура с кнопкой «Главное меню».
    """
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Главное меню", color=VkKeyboardColor.SECONDARY, payload={"cmd": CMD_START})
    return keyboard
