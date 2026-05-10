import yaml
import json
import re

from dotenv import dotenv_values
from datetime import datetime, date


def get_yaml(path) -> dict:
    with open(path) as file:
        return yaml.safe_load(file)

def get_env() -> dict:
    return dotenv_values(".env")


def parse_date(timestamp: int | None) -> date | None:
    if timestamp:
        return datetime.fromtimestamp(timestamp).date()
    return None

def parse_llm_json(text: str) -> dict:
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)