import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DB_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/db.sqlite3"
    SECRET_KEY: str
    ALGORITHM: str
    VALID_CURRENCIES: list = ["usd", "eur"]
    ERROR_MESSAGES: dict = {
        "currency_type": "Некорректный тип валюты. Используйте 'usd' или 'eur'.",
        "range": "Неверно задан диапазон.",
        "not_found": "Не найдены курсы валют.",
        "bank_not_found": "Банк не найден."
    }
    CURRENCY_FIELDS: dict = {
        'usd': {'buy': 'usd_buy', 'sell': 'usd_sell'},
        'eur': {'buy': 'eur_buy', 'sell': 'eur_sell'}
    }
    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env")


# Получаем параметры для загрузки переменных среды
settings = Settings()
database_url = settings.DB_URL
