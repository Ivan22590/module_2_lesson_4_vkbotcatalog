"""Точка входа ВКонтакте-бота ортопедического салона.

Запуск: ``python bot.py``.

Бот читает токен сообщества из файла ``.env``, определяет ID сообщества
(автоматически или из переменной ``VK_GROUP_ID``) и слушает события
Bots Long Poll API.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.exceptions import ApiError, VkApiError
from vk_api.utils import get_random_id

from config import Config, ConfigError, load_config, setup_logging
from handlers.commands import ERROR_TEXT, handle_message
from keyboards.menus import main_menu_keyboard

logger = logging.getLogger("bot")

MAX_MESSAGE_LENGTH = 4096  # ограничение ВКонтакте на длину сообщения
RECONNECT_DELAY = 5  # пауза перед переподключением к Long Poll, сек
FATAL_API_CODES = frozenset({5, 15})  # неверный токен / нет доступа
CHAT_BOT_FEATURE_CODE = 912  # в сообществе отключены «Возможности ботов»
CHAT_BOT_FEATURE_HINT = (
    "ВКонтакте запретил отправку сообщений: в сообществе отключены "
    "«Возможности ботов». Включите их: Управление сообществом → Сообщения → "
    "Настройки ботов → «Возможности ботов»."
)


def resolve_group_id(session: vk_api.VkApi, configured: int | None) -> int:
    """Определяет ID сообщества: из конфигурации или автоматически через API.

    :param session: сессия ВКонтакте с токеном сообщества;
    :param configured: ID из переменной ``VK_GROUP_ID`` или None;
    :return: ID сообщества;
    :raises ConfigError: если ID не задан и получить его автоматически не удалось.
    """
    if configured is not None:
        return configured

    response = session.method("groups.getById")

    # В разных версиях API ответ — список групп или объект с полем groups/items
    if isinstance(response, dict):
        groups = response.get("groups") or response.get("items") or []
    else:
        groups = response

    if not groups:
        raise ConfigError(
            "Не удалось автоматически определить ID сообщества. "
            "Добавьте в файл .env строку: VK_GROUP_ID=ваш_id"
        )

    group_id = int(groups[0]["id"])
    logger.info("ID сообщества получен автоматически: %s (%s)", group_id, groups[0].get("name"))
    return group_id


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Разбивает длинный текст на части не длиннее limit по границам строк.

    :param text: исходный текст сообщения;
    :param limit: максимальная длина одной части;
    :return: список частей текста.
    """
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = line if not current else f"{current}\n{line}"
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        # Одна строка длиннее лимита — режем ее принудительно
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current = line
    if current:
        chunks.append(current)
    return chunks


def send_message(
    vk: vk_api.VkApiMethod,
    peer_id: int,
    text: str,
    keyboard: vk_api.keyboard.VkKeyboard,
) -> None:
    """Отправляет сообщение пользователю с клавиатурой.

    Длинные тексты разбиваются на части, каждая отправляется отдельным
    сообщением с обязательным параметром ``random_id``.

    :param vk: объект API ВКонтакте;
    :param id получателя;
    :param text: текст сообщения;
    :param keyboard: клавиатура сообщения;
    :raises vk_api.exceptions.ApiError: при ошибке VK API.
    """
    keyboard_json = keyboard.get_keyboard()
    for chunk in split_message(text):
        vk.messages.send(
            peer_id=peer_id,
            message=chunk,
            random_id=get_random_id(),
            keyboard=keyboard_json,
        )


def parse_payload(message: dict[str, Any]) -> dict[str, Any] | None:
    """Разбирает payload кнопки из объекта сообщения.

    Payload приходит JSON-строкой; поврежденный payload не должен ронять бота.

    :param message: объект сообщения из события;
    :return: словарь payload или None, если payload отсутствует или невалиден.
    """
    raw = message.get("payload") or message.get("message_payload")
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("Некорректный payload: %.100s", raw)
        return None
    return parsed if isinstance(parsed, dict) else None


def handle_event(vk: vk_api.VkApiMethod, event: Any) -> None:
    """Обрабатывает одно событие Long Poll.

    На сообщение пользователя формируется ответ через роутер
    и отправляется с клавиатурой. Ошибки не прерывают работу бота.

    :param vk: объект API ВКонтакте;
    :param event: событие Long Poll.
    """
    if event.type != VkBotEventType.MESSAGE_NEW:
        return

    message = event.message
    if message is None:
        return

    # Игнорируем сообщения от сообществ, чтобы не зациклиться
    if getattr(event, "from_group", False):
        return

    peer_id = message.get("peer_id")
    if not peer_id:
        logger.warning("Событие без peer_id пропущено")
        return

    text = message.get("text") or None
    payload = parse_payload(message)
    logger.info("Входящее сообщение: peer_id=%s, text=%.60r, payload=%s", peer_id, text, payload)

    reply_text, keyboard = _safe_reply(text, payload)

    try:
        send_message(vk, peer_id, reply_text, keyboard)
    except ApiError as exc:
        logger.error("Не удалось отправить сообщение peer_id=%s: %s", peer_id, exc)
        if exc.code == CHAT_BOT_FEATURE_CODE:
            # Ответное уведомление упадет с той же ошибкой — не пробуем
            logger.error(CHAT_BOT_FEATURE_HINT)
            return
        _try_send_error_notice(vk, peer_id)
    except VkApiError:
        logger.exception("Сетевая ошибка при отправке peer_id=%s", peer_id)


def _safe_reply(
    text: str | None, payload: dict[str, Any] | None
) -> tuple[str, vk_api.keyboard.VkKeyboard]:
    """Формирует ответ, перехватывая любые ошибки роутера.

    :param text: текст входящего сообщения;
    :param payload: разобранный payload кнопки;
    :return: пара (текст ответа, клавиатура).
    """
    try:
        return handle_message(text, payload)
    except Exception:
        logger.exception("Ошибка роутера сообщений")
        return ERROR_TEXT, main_menu_keyboard()


def _try_send_error_notice(vk: vk_api.VkApiMethod, peer_id: int) -> None:
    """Best-effort отправка дружелюбного сообщения об ошибке.

    :param vk: объект API ВКонтакте;
    :param id получателя.
    """
    try:
        send_message(vk, peer_id, ERROR_TEXT, main_menu_keyboard())
    except Exception:
        logger.exception("Не удалось отправить уведомление об ошибке peer_id=%s", peer_id)


def run_bot(config: Config) -> int:
    """Создает сессию, определяет ID сообщества и запускает цикл Long Poll.

    При обрыве соединения бот переподключается с паузой.

    :param config: конфигурация бота;
    :return: код завершения процесса.
    """
    session = vk_api.VkApi(token=config.token)

    try:
        group_id = resolve_group_id(session, config.group_id)
    except ApiError as exc:
        logger.error(
            "ВКонтакте отклонил запрос: %s. Проверьте токен в файле .env.", exc
        )
        return 1
    except ConfigError as exc:
        logger.error("%s", exc)
        return 1

    vk = session.get_api()
    logger.info("Бот запускается, group_id=%s", group_id)

    while True:
        try:
            longpoll = VkBotLongPoll(session, group_id)
            logger.info("Long Poll запущен, ожидание сообщений...")
            for event in longpoll.listen():
                handle_event(vk, event)
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем.")
            return 0
        except ApiError as exc:
            if exc.code in FATAL_API_CODES:
                logger.error(
                    "Нет доступа к API: %s. Проверьте токен в .env и настройки "
                    "сообщества (сообщения и Long Poll должны быть включены).",
                    exc,
                )
                return 1
            logger.error("Ошибка VK API: %s. Переподключение через %s с", exc, RECONNECT_DELAY)
            time.sleep(RECONNECT_DELAY)
        except VkApiError:
            logger.exception(
                "Сетевая ошибка Long Poll, переподключение через %s с", RECONNECT_DELAY
            )
            time.sleep(RECONNECT_DELAY)
        except Exception:
            logger.exception("Непредвиденная ошибка, переподключение через %s с", RECONNECT_DELAY)
            time.sleep(RECONNECT_DELAY)


def main() -> int:
    """Точка входа бота.

    :return: код завершения процесса (0 — успех).
    """
    setup_logging()

    try:
        config = load_config()
    except ConfigError as exc:
        logger.error("%s", exc)
        return 1

    return run_bot(config)


if __name__ == "__main__":
    sys.exit(main())
