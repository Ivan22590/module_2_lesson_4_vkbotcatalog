"""Обработка входящих сообщений и построение ответов.

Роутер принимает текст сообщения и payload кнопки, а возвращает
текст ответа и клавиатуру.
"""

from __future__ import annotations

import logging
from typing import Any

from vk_api.keyboard import VkKeyboard

from data.about import build_about_text
from data.assortment import CATEGORIES, build_assortment_list, build_category_card, get_category
from data.doctor import build_booking_text, build_doctor_card
from data.salons import SALONS, build_salons_list
from data.services import SERVICES, build_service_card, build_services_list, get_service
from keyboards.menus import (
    CMD_ABOUT,
    CMD_ASSORTMENT,
    CMD_BOOK,
    CMD_CATEGORY,
    CMD_DOCTOR,
    CMD_SALONS,
    CMD_SERVICE,
    CMD_SERVICES,
    CMD_START,
    assortment_keyboard,
    back_to_main_keyboard,
    booking_keyboard,
    category_card_keyboard,
    doctor_keyboard,
    main_menu_keyboard,
    salons_keyboard,
    service_card_keyboard,
    services_keyboard,
)

logger = logging.getLogger(__name__)

# Текстовые команды, распознаваемые помимо payload
START_WORDS = frozenset({"старт", "начать", "/start", "start", "меню", "menu"})

TEXT_COMMANDS: dict[str, str] = {
    "услуги": CMD_SERVICES,
    "услуга": CMD_SERVICES,
    "каталог услуг": CMD_SERVICES,
    "ассортимент": CMD_ASSORTMENT,
    "каталог": CMD_ASSORTMENT,
    "товары": CMD_ASSORTMENT,
    "салоны": CMD_SALONS,
    "салон": CMD_SALONS,
    "адреса": CMD_SALONS,
    "магазины": CMD_SALONS,
    "врач": CMD_DOCTOR,
    "ортопед": CMD_DOCTOR,
    "врач-ортопед": CMD_DOCTOR,
    "запись": CMD_BOOK,
    "записаться": CMD_BOOK,
    "запись к врачу": CMD_BOOK,
    "о центре": CMD_ABOUT,
    "о нас": CMD_ABOUT,
    "о салоне": CMD_ABOUT,
    "главное меню": CMD_START,
    "назад в услуги": CMD_SERVICES,
    "назад к услугам": CMD_SERVICES,
    "назад к врачу": CMD_DOCTOR,
}

GREETING_TEXT = (
    "Здравствуйте! Это бот ортоцентра «Авиценна» — Выборг, avicenna-vbg.ru.\n"
    "\n"
    "Мы помогаем людям с проблемами опорно-двигательного аппарата: "
    "приём врача-ортопеда, компьютерная диагностика стоп и осанки, "
    "индивидуальные ортопедические стельки и ортопедические изделия "
    "в салонах города.\n"
    "\n"
    "Выберите пункт меню ниже."
)

UNKNOWN_TEXT = (
    "Я не совсем понял ваше сообщение.\n"
    "Воспользуйтесь кнопками меню или напишите «начать»."
)

ERROR_TEXT = "Произошла ошибка. Попробуйте еще раз чуть позже или свяжитесь с нами по телефону."

EMPTY_SERVICES_TEXT = "Список услуг пока пуст. Посмотрите раздел «Врач-ортопед» — там есть контакты для записи."

EMPTY_CATEGORIES_TEXT = "Раздел ассортимента пока пуст. Посмотрите раздел «Салоны и адреса»."

SERVICE_NOT_FOUND_TEXT = "Такой услуги нет в списке. Выберите услугу из списка."

CATEGORY_NOT_FOUND_TEXT = "Такого раздела нет в ассортименте. Выберите раздел из списка."


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
        if command == CMD_SERVICES:
            return _handle_services()
        if command == CMD_SERVICE:
            return _handle_service(command_arg)
        if command == CMD_ASSORTMENT:
            return _handle_assortment()
        if command == CMD_CATEGORY:
            return _handle_category(command_arg)
        if command == CMD_SALONS:
            return _handle_salons()
        if command == CMD_DOCTOR:
            return _handle_doctor()
        if command == CMD_BOOK:
            return _handle_book()
        if command == CMD_ABOUT:
            return _handle_about()
    except Exception:
        logger.exception("Ошибка при обработке команды %r", command)
        return ERROR_TEXT, main_menu_keyboard()

    return UNKNOWN_TEXT, main_menu_keyboard()


def _resolve_command(text: str | None, payload: dict[str, Any] | None) -> tuple[str, str | None]:
    """Определяет команду по payload кнопки или по тексту сообщения.

    :param text: текст входящего сообщения;
    :param payload: разобранный payload кнопки;
    :return: пара (команда, аргумент команды); аргумент — id услуги
        или раздела, либо None.
    """
    if payload:
        command = payload.get("cmd")
        if command in (CMD_SERVICE, CMD_CATEGORY):
            item_id = payload.get("id")
            return str(command), str(item_id) if item_id else None
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


def _handle_services() -> tuple[str, VkKeyboard]:
    """Формирует список услуг ортоцентра.

    :return: пара (текст списка, клавиатура списка услуг).
    """
    if not SERVICES:
        return EMPTY_SERVICES_TEXT, main_menu_keyboard()
    return build_services_list(), services_keyboard(SERVICES)


def _handle_service(service_id: str | None) -> tuple[str, VkKeyboard]:
    """Формирует карточку выбранной услуги.

    :param service_id: идентификатор услуги из payload кнопки;
    :return: пара (текст карточки, клавиатура карточки).
    """
    if not service_id:
        logger.warning("Payload команды %r без id", CMD_SERVICE)
        return SERVICE_NOT_FOUND_TEXT, services_keyboard(SERVICES)

    service = get_service(service_id)
    if service is None:
        logger.warning("Услуга не найдена: id=%r", service_id)
        return SERVICE_NOT_FOUND_TEXT, services_keyboard(SERVICES)

    return build_service_card(service), service_card_keyboard(service_id)


def _handle_assortment() -> tuple[str, VkKeyboard]:
    """Формирует список товарных разделов ассортимента.

    :return: пара (текст списка, клавиатура ассортимента).
    """
    if not CATEGORIES:
        return EMPTY_CATEGORIES_TEXT, main_menu_keyboard()
    return build_assortment_list(), assortment_keyboard(CATEGORIES)


def _handle_category(category_id: str | None) -> tuple[str, VkKeyboard]:
    """Формирует карточку выбранного товарного раздела.

    :param category_id: идентификатор раздела из payload кнопки;
    :return: пара (текст карточки, клавиатура карточки).
    """
    if not category_id:
        logger.warning("Payload команды %r без id", CMD_CATEGORY)
        return CATEGORY_NOT_FOUND_TEXT, assortment_keyboard(CATEGORIES)

    category = get_category(category_id)
    if category is None:
        logger.warning("Раздел не найден: id=%r", category_id)
        return CATEGORY_NOT_FOUND_TEXT, assortment_keyboard(CATEGORIES)

    return build_category_card(category), category_card_keyboard(category_id)


def _handle_salons() -> tuple[str, VkKeyboard]:
    """Формирует список салонов и магазинов с адресами и графиком.

    :return: пара (текст со списком, клавиатура салонов).
    """
    if not SALONS:
        return EMPTY_CATEGORIES_TEXT, main_menu_keyboard()
    return build_salons_list(), salons_keyboard(SALONS)


def _handle_doctor() -> tuple[str, VkKeyboard]:
    """Формирует карточку врача-ортопеда.

    :return: пара (текст карточки, клавиатура врача).
    """
    return build_doctor_card(), doctor_keyboard()


def _handle_book() -> tuple[str, VkKeyboard]:
    """Формирует сообщение с инструкцией по записи к врачу.

    :return: пара (текст записи, клавиатура записи).
    """
    return build_booking_text(), booking_keyboard()


def _handle_about() -> tuple[str, VkKeyboard]:
    """Формирует описание ортоцентра.

    :return: пара (текст о центре, главное меню).
    """
    return build_about_text(), back_to_main_keyboard()
