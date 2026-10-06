"""Смоук-проверка бота без подключения к ВКонтакте.

Прогоняет все payload-команды и текстовые команды через роутер,
проверяет длину подписей кнопок и валидность JSON клавиатур.

Запуск:  .venv\\Scripts\\python.exe smoke_check.py
"""

from __future__ import annotations

import json
import sys

from data.assortment import CATEGORIES, get_button_label as category_label
from data.services import SERVICES, get_button_label as service_label
from handlers.commands import handle_message
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
)

MAX_LABEL = 40
errors: list[str] = []
seen: set[str] = set()
queue: list[dict] = [
    {"cmd": CMD_START},
    {"cmd": CMD_SERVICES},
    {"cmd": CMD_ASSORTMENT},
    {"cmd": CMD_SALONS},
    {"cmd": CMD_DOCTOR},
    {"cmd": CMD_BOOK},
    {"cmd": CMD_ABOUT},
]

# 1. Все услуги и разделы должны иметь уникальные подписи кнопок <= 40 символов
service_labels = [service_label(s) for s in SERVICES]
category_labels = [category_label(c) for c in CATEGORIES]
if len(set(service_labels)) != len(service_labels):
    errors.append("Повторяющиеся подписи кнопок услуг")
if len(set(category_labels)) != len(category_labels):
    errors.append("Повторяющиеся подписи кнопок разделов")
for label in service_labels + category_labels:
    if len(label) > MAX_LABEL:
        errors.append(f"Подпись кнопки длиннее {MAX_LABEL}: {label!r}")
queue.extend({"cmd": CMD_SERVICE, "id": s["id"]} for s in SERVICES)
queue.extend({"cmd": CMD_CATEGORY, "id": c["id"]} for c in CATEGORIES)

# 2. Обход всех payload-кнопок (включая кнопки, найденные в клавиатурах)
while queue:
    payload = queue.pop()
    key = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    if key in seen:
        continue
    seen.add(key)

    try:
        text, keyboard = handle_message(None, payload)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Исключение для payload={payload}: {exc!r}")
        continue

    if not text or not text.strip():
        errors.append(f"Пустой текст ответа для payload={payload}")
    if len(text) > 4096:
        errors.append(f"Текст длиннее 4096 для payload={payload} ({len(text)})")

    try:
        kb = json.loads(keyboard.get_keyboard())
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Невалидный JSON клавиатуры для payload={payload}: {exc!r}")
        continue

    rows = kb.get("buttons") or []
    if not rows:
        errors.append(f"Пустая клавиатура для payload={payload}")
    for row in rows:
        if not row:
            errors.append(f"Пустая строка в клавиатуре для payload={payload}")
        if len(row) > 5:
            errors.append(f"Больше 5 кнопок в строке для payload={payload}")
        for button in row:
            action = button.get("action") or {}
            label = action.get("label", "")
            if len(label) > MAX_LABEL:
                errors.append(f"Подпись длиннее {MAX_LABEL}: {label!r}")
            if action.get("type") == "open_link":
                link = str(action.get("link", ""))
                if not link.startswith("https://"):
                    errors.append(f"Кнопка-ссылка не https: {link}")
                if len(link) > 100:
                    errors.append(f"Ссылка длиннее 100 символов ({len(link)}): {link}")
                if not link.isascii():
                    errors.append(f"Ссылка с не-ASCII символами: {link}")
            btn_payload = action.get("payload")
            if btn_payload:
                if isinstance(btn_payload, str):
                    btn_payload = json.loads(btn_payload)
                queue.append(btn_payload)

# 3. Текстовые команды
text_cases = [
    "старт", "начать", "/start", "услуги", "ассортимент", "салоны",
    "адреса", "врач", "запись", "записаться", "о центре", "о нас",
    "главное меню", "привет, что умеешь?",
]
for case in text_cases:
    try:
        text, keyboard = handle_message(case, None)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Исключение для текста {case!r}: {exc!r}")
        continue
    if not text or not text.strip():
        errors.append(f"Пустой ответ на текст {case!r}")
    json.loads(keyboard.get_keyboard())

# 4. Поврежденный payload не должен ронять роутера
for bad in [{"cmd": CMD_SERVICE}, {"cmd": CMD_CATEGORY}, {"cmd": "unknown"}, {"id": "x"}]:
    try:
        text, _ = handle_message(None, bad)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Исключение для payload={bad}: {exc!r}")
        continue
    if not text:
        errors.append(f"Пустой ответ для payload={bad}")

print(f"Проверено payload-состояний: {len(seen)}")
print(f"Услуг: {len(SERVICES)}, разделов ассортимента: {len(CATEGORIES)}")
if errors:
    print("ОШИБКИ:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
print("OK: ошибок не найдено")
