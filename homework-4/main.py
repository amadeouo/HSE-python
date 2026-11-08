import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field, PastDate, field_validator


app = FastAPI(title="Обращения абонентов")
DATA_DIR = Path(__file__).resolve().parent / "requests"
NAME_PATTERN = r"[А-ЯЁ][а-яё]*"
PHONE_PATTERN = r"\+[1-9][0-9]{7,14}"

Reason = Literal[
    "нет доступа к сети",
    "не работает телефон",
    "не приходят письма",
]


class SubscriberRequest(BaseModel):
    last_name: str
    first_name: str
    birth_date: PastDate
    phone: str
    email: EmailStr
    reasons: list[Reason] = Field(min_length=1)
    problem_detected_at: datetime

    @field_validator("last_name", "first_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not re.fullmatch(NAME_PATTERN, value):
            raise ValueError(
                "Используйте только русские буквы: первая заглавная, остальные строчные"
            )
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.fullmatch(PHONE_PATTERN, value):
            raise ValueError("Телефон должен содержать + и от 8 до 15 цифр")
        return value

    @field_validator("birth_date", "problem_detected_at", mode="before")
    @classmethod
    def validate_date_format(cls, value):
        if not isinstance(value, str):
            raise ValueError("Передайте дату строкой в формате ISO 8601")
        return value

    @field_validator("problem_detected_at")
    @classmethod
    def validate_problem_date(cls, value: datetime) -> datetime:
        if value > datetime.now(tz=value.tzinfo):
            raise ValueError("Дата обнаружения проблемы не может быть в будущем")
        return value


@app.post("/requests/", status_code=201)
def create_request(data: SubscriberRequest):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    request_id = uuid4().hex
    file_path = DATA_DIR / f"{request_id}.json"
    file_path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
    return {"id": request_id, "message": "Обращение сохранено"}
