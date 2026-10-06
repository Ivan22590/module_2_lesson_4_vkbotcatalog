"""Врач-ортопед ортоцентра «Авиценна» и запись на приём.

Данные взяты со страницы «Врач-ортопед» сайта
https://avicenna-vbg.ru/adress/1-vrach-ortoped.html
"""

from __future__ import annotations

from typing import TypedDict


class Doctor(TypedDict):
    """Карточка врача.

    :param name: имя и фамилия врача;
    :param specialty: специальность;
    :param license_number: номер действующей медицинской лицензии;
    :param email: электронная почта;
    :param phone: телефон для записи;
    :param address: адрес кабинета;
    :param site_url: страница врача на сайте;
    :param prodoctorov_url: страница врача на «ПроДокторов».
    """

    name: str
    specialty: str
    license_number: str
    email: str
    phone: str
    address: str
    site_url: str
    prodoctorov_url: str


DOCTOR: Doctor = {
    "name": "Левдиков Андрей Викторович",
    "specialty": "Врач ортопед-травматолог",
    "license_number": "Л041-01149-47/00383623",
    "email": "ortodiagnost@mail.ru",
    "phone": "+7 (921) 325-52-90",
    "address": "г. Выборг, бульвар Кутузова, д. 9, ОРТО ЦЕНТР «Авиценна»",
    "site_url": "https://avicenna-vbg.ru/adress/1-vrach-ortoped.html",
    "prodoctorov_url": "https://prodoctorov.ru/vyborg/vrach/468345-levdikov/",
}

# Сообщения сообщества ВКонтакте (раздел «Клуб здоровья Авиценна» на сайте)
COMMUNITY_MESSAGES_URL = "https://vk.me/avicenna_vyborg"
COMMUNITY_URL = "https://vk.com/avicenna_vyborg"

BOOKING_HINT = (
    "Запись к врачу-ортопеду осуществляется по телефону "
    f"{DOCTOR['phone']} или через сообщения сообщества ВКонтакте. "
    "Кабинет врача находится по адресу: "
    f"{DOCTOR['address']}.\n"
    "\n"
    "График работы салона на бульваре Кутузова, 9:\n"
    "пн-сб 10:00-19:00, вс 10:00-18:00, без обеда."
)


def build_doctor_card() -> str:
    """Формирует карточку врача-ортопеда.

    :return: текст карточки для отправки сообщением.
    """
    return "\n".join(
        [
            "Врач-ортопед ортоцентра «Авиценна»",
            "",
            f"Врач: {DOCTOR['name']}",
            f"Специальность: {DOCTOR['specialty']}",
            f"Лицензия: {DOCTOR['license_number']}",
            "",
            "Врач консультирует по всем вопросам консервативного лечения "
            "заболеваний опорно-двигательного аппарата и последствий травм, "
            "проводит компьютерную диагностику стоп и осанки, изготавливает "
            "индивидуальные ортопедические стельки.",
            "",
            f"Телефон: {DOCTOR['phone']}",
            f"Электронная почта: {DOCTOR['email']}",
            f"Кабинет: {DOCTOR['address']}",
        ]
    )


def build_booking_text() -> str:
    """Формирует сообщение с инструкцией по записи к врачу.

    :return: текст записи для отправки сообщением.
    """
    return "\n".join(
        [
            "Запись к врачу-ортопеду",
            "",
            BOOKING_HINT,
            "",
            f"Телефон: {DOCTOR['phone']}",
            f"Почта: {DOCTOR['email']}",
            "",
            "Нажмите «Написать в сообщения» — мы ответим вам в сообщениях "
            "сообщества, либо откройте страницу врача на сайте.",
        ]
    )
