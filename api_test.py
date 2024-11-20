from typing import Tuple

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dao import CurrencyRateDAO
from app.config import settings


def validate_currency_type(currency_type: str) -> str:
    """Проверяет корректность типа валюты."""
    if currency_type.lower() not in settings.VALID_CURRENCIES:
        raise HTTPException(status_code=400, detail=settings.ERROR_MESSAGES["currency_type"])
    return currency_type.lower()


def validate_range(min_val: float, max_val: float) -> None:
    """Проверяет корректность диапазона значений."""
    if min_val > max_val:
        raise HTTPException(status_code=400, detail=settings.ERROR_MESSAGES["range"])


async def get_currency_ranges(
        currency_type: str,
        operation: str,
        session: AsyncSession
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Получает диапазоны для основной и альтернативной валюты."""
    other_currency = 'eur' if currency_type == 'usd' else 'usd'

    requested_range = await CurrencyRateDAO.get_currency_range(
        currency=currency_type,
        operation=operation,
        session=session
    )
    other_range = await CurrencyRateDAO.get_currency_range(
        currency=other_currency,
        operation=operation,
        session=session
    )

    return requested_range, other_range
