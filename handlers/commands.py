"""Обработка входящих сообщений и построение ответов.

Роутер принимает текст сообщения и payload кнопки, а возвращает
текст ответа и клавиатуру.
"""

from __future__ import annotations

import logging
from typing import Any

from vk_api.keyboard import VkKeyboard

from data.services import (
    ABOUT_SALON,
    SERVICES,
    build_catalog_list,
    build_manager_card,
    build_price_list,
    build_service_card,
    get_service,
)
from keyboards.menus import (
    CMD_ABOUT,
    CMD_CATALOG,
    CMD_MANAGER,
    CMD_PRICE,
    CMD_SERVICE,
    CMD_START,
    back_to_main_keyboard,
    catalog_keyboard,
    main_menu_keyboard,
    manager_keyboard,
    service_card_keyboard,
)

logger = logging.getLogger(__name__)

# Текстовые команды, распознаваемые помимо payload
START_WORDS = frozenset({"старт", "начать", "/start", "start", "меню", "menu"})

TEXT_COMMANDS: dict[str, str] = {
    "каталог услуг": CMD_CATALOG,
    "каталог": CMD_CATALOG,
    "прайс-лист": CMD_PRICE,
    "прайс": CMD_PRICE,
    "связаться с менеджером": CMD_MANAGER,
    "менеджер": CMD_MANAGER,
    "о салоне": CMD_ABOUT,
    "главное меню": CMD_START,
    "назад в каталог": CMD_CATALOG,
}

GREETING_TEXT = (
    "Здравствуйте! Это бот ортопедического салона «Здоровые шаги».\n"
    "\n"
    "Здесь вы можете посмотреть каталог услуг, узнать цены, "
    "получить подробную информацию об услуге и связаться с менеджером.\n"
    "\n"
    "Выберите пункт меню ниже."
)

UNKNOWN_TEXT = (
    "Я не совсем понял ваше сообщение.\n"
    "Воспользуйтесь кнопками меню или напишите «начать»."
)

ERROR_TEXT = "Произошла ошибка. Попробуйте еще раз чуть позже или свяжитесь с менеджером."

EMPTY_SERVICES_TEXT = "Каталог услуг пока пуст. Свяжитесь с менеджером, чтобы узнать подробности."

SERVICE_NOT_FOUND_TEXT = "Такой услуги нет в каталоге. Выберите услугу из списка."


def handle_message(text: str | None, payload: dict[str, Any] | None) -> tuple[str, VkKeyboard]:
    """Обрабатывает входящее сообщение и формирует ответ.

    Приоритет у payload кнопки; если payload нет, сообщение разбирается
    как текстовая команда. Неизвестные сообщения получают вежливый ответ
    и главное меню.

    :param text: текст входящего сообщения (может быть пустым);
    :param payload: разобранный payload кнопки или None;
    :return: пара (текст ответа, клавиатура).
    """
    command, command_arg = _resolve_command(text, payload)

    try:
        if command == CMD_START:
            return _handle_start()
        if command == CMD_CATALOG:
            return _handle_catalog()
        if command == CMD_PRICE:
            return _handle_price()
        if command == CMD_MANAGER:
            return _handle_manager()
        if command == CMD_ABOUT:
            return _handle_about()
        if command == CMD_SERVICE:
            return _handle_service(command_arg)
    except Exception:
        logger.exception("Ошибка при обработке команды %r", command)
        return ERROR_TEXT, main_menu_keyboard()

    return UNKNOWN_TEXT, main_menu_keyboard()


def _resolve_command(text: str | None, payload: dict[str, Any] | None) -> tuple[str, str | None]:
    """Определяет команду по payload кнопки или по тексту сообщения.

    :param text: текст входящего сообщения;
    :param payload: разобранный payload кнопки;
    :return: пара (команда, аргумент команды); аргумент — id услуги или None.
    """
    if payload:
        command = payload.get("cmd")
        if command == CMD_SERVICE:
            service_id = payload.get("id")
            return CMD_SERVICE, str(service_id) if service_id else None
        if isinstance(command, str) and command:
            return command, None

    normalized = (text or "").strip().lower()
    if not normalized:
        return "", None
    if normalized in START_WORDS:
        return CMD_START, None

    return TEXT_COMMANDS.get(normalized, ""), None


def _handle_start() -> tuple[str, VkKeyboard]:
    """Формирует приветствие и главное меню.

    :return: пара (текст приветствия, главное меню).
    """
    return GREETING_TEXT, main_menu_keyboard()


def _handle_catalog() -> tuple[str, VkKeyboard]:
    """Формирует каталог услуг.

    :return: пара (текст каталога, клавиатура каталога).
    """
    if not SERVICES:
        return EMPTY_SERVICES_TEXT, main_menu_keyboard()
    return build_catalog_list(), catalog_keyboard(SERVICES)


def _handle_price() -> tuple[str, VkKeyboard]:
    """Формирует прайс-лист из базы знаний.

    :return: пара (текст прайс-листа, главное меню).
    """
    if not SERVICES:
        return EMPTY_SERVICES_TEXT, main_menu_keyboard()
    return build_price_list(), main_menu_keyboard()


def _handle_manager() -> tuple[str, VkKeyboard]:
    """Формирует контакты менеджера.

    :return: пара (текст с контактами, клавиатура менеджера).
    """
    return build_manager_card(), manager_keyboard()


def _handle_about() -> tuple[str, VkKeyboard]:
    """Формирует описание салона.

    :return: пара (текст о салоне, главное меню).
    """
    return ABOUT_SALON, back_to_main_keyboard()


def _handle_service(service_id: str | None) -> tuple[str, VkKeyboard]:
    """Формирует карточку выбранной услуги.

    :param id: идентификатор услуги из payload кнопки;
    :return: пара (текст карточки, клавиатура карточки).
    """
    if not service_id:
        logger.warning("Повестка service без id услуги")
        return SERVICE_NOT_FOUND_TEXT, catalog_keyboard(SERVICES)

    service = get_service(service_id)
    if service is None:
        logger.warning("Услуга не найдена: id=%r", service_id)
        return SERVICE_NOT_FOUND_TEXT, catalog_keyboard(SERVICES)

    return build_service_card(service), service_card_keyboard(service_id)
