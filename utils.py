import yaml
import json
import re
import logging

from dotenv import dotenv_values
from datetime import datetime, date

logger = logging.getLogger(__name__)


def get_yaml(path) -> dict:
    with open(path) as file:
        return yaml.safe_load(file)

def get_env() -> dict:
    return dotenv_values(".env")


def parse_date(value: int | float | str | None) -> date | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).date()
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
    except ValueError:
        logger.warning("Не удалось распарсить дату: %s", value)
        return None

def parse_llm_json(text: str) -> dict | None:
    clean = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.warning("Не удалось распарсить JSON: %s\nТекст: %s", e, clean)
        return None