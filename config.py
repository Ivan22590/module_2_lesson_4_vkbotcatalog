"""Конфигурация бота: чтение переменных окружения и настройка логирования."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
LOG_PATH = BASE_DIR / "bot.log"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

TOKEN_VAR = "VK_GROUP_TOKEN"
GROUP_ID_VAR = "VK_GROUP_ID"
PLACEHOLDER_TOKEN = "your_group_token_here"


class ConfigError(Exception):
    """Ошибка конфигурации, которую нужно показать пользователю понятным текстом."""


@dataclass(frozen=True)
class Config:
    """Настройки бота, загруженные из переменных окружения.

    :param token: токен доступа сообщества ВКонтакте;
    :param group_id: ID сообщества или None, если нужно получить его автоматически.
    """

    token: str
    group_id: int | None = None


def setup_logging() -> None:
    """Настраивает логирование в консоль и в файл ``bot.log`` (UTF-8).

    Файл нужен, чтобы можно было посмотреть историю запуска, когда консоль
    недоступна: туда попадают входящие сообщения, отправленные ответы
    и все ошибки. Файл ограничен по размеру, старые копии — ``bot.log.N``.

    Токен в логи никогда не выводится.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass

    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    log_file = RotatingFileHandler(
        LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    log_file.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console, log_file])


def load_config() -> Config:
    """Загружает настройки бота из файла ``.env`` (и из окружения процесса).

    :return: заполненную конфигурацию;
    :raises ConfigError: если файл ``.env`` отсутствует, токен не задан
        или оставлен текст-заглушка.
    """
    env_exists = ENV_PATH.exists()
    load_dotenv(ENV_PATH)

    token = os.getenv(TOKEN_VAR, "").strip()
    if not token:
        if not env_exists:
            raise ConfigError(
                f"Файл .env не найден ({ENV_PATH}). "
                f"Скопируйте .env.example в .env и укажите в нем {TOKEN_VAR}=ваш_токен."
            )
        raise ConfigError(
            f"В файле .env не найдена переменная {TOKEN_VAR}. "
            f"Добавьте строку {TOKEN_VAR}=ваш_токен."
        )

    if token == PLACEHOLDER_TOKEN:
        raise ConfigError(
            f"В файле .env оставлен заглушка вместо токена. "
            f"Замените {PLACEHOLDER_TOKEN} на токен сообщества."
        )

    group_id = _parse_group_id(os.getenv(GROUP_ID_VAR, ""))
    return Config(token=token, group_id=group_id)


def _parse_group_id(raw: str) -> int | None:
    """Разбирает необязательную переменную ``VK_GROUP_ID``.

    :param raw: строка из переменной окружения (может быть пустой);
    :return: ID сообщества или None, если переменная не задана;
    :raises ConfigError: если значение не является числом.
    """
    raw = raw.strip()
    if not raw:
        return None
    if not raw.isdigit():
        raise ConfigError(f"Переменная {GROUP_ID_VAR} должна быть числом, получено: {raw!r}.")
    return int(raw)
