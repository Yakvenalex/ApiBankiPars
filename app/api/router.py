from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.utils import validate_range, validate_currency_type, get_currency_ranges
from app.auth.dependencies import get_current_user, get_current_admin_user
from app.auth.models import User
from app.config import settings
from app.dao.session_maker import SessionDep
from app.api.dao import CurrencyRateDAO
from app.api.schemas import (
    CurrencyRateSchema, BankNameSchema, CurrencyRangeFilterSchema,
    AdminCurrencySchema, CurrencySaleRangeFilterSchema, BestRateResponse
)

router = APIRouter(prefix='/api', tags=['API'])


@router.get("/all_currency/")
async def get_all_currency(
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> List[CurrencyRateSchema]:
    """Возвращает актуальные курсы валют всех банков."""
    return await CurrencyRateDAO.find_all(session=session, filters=None)


@router.get("/all_currency_admin/")
async def get_all_currency_admin(
        user_data: User = Depends(get_current_admin_user),
        session: AsyncSession = SessionDep
) -> List[AdminCurrencySchema]:
    """Возвращает расширенную информацию о курсах валют (только для админов)."""
    return await CurrencyRateDAO.find_all(session=session, filters=None)


@router.get("/currency_by_bank/{bank_en}")
async def get_currency_by_bank(
        bank_en: str,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> CurrencyRateSchema | None:
    """Возвращает курсы валют конкретного банка по его английскому названию."""
    currencies = await CurrencyRateDAO.find_one_or_none(session=session, filters=BankNameSchema(bank_en=bank_en))
    if not currencies:
        raise HTTPException(status_code=404, detail=settings.ERROR_MESSAGES["bank_not_found"])
    return currencies


@router.post("/currency_in_purchase_range/")
async def get_currency_in_purchase_range(
        filter_data: CurrencyRangeFilterSchema,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> List[CurrencyRateSchema]:
    """Возвращает курсы валют, находящиеся в заданном диапазоне цен покупки для USD и EUR."""
    validate_range(filter_data.usd_min, filter_data.usd_max)
    validate_range(filter_data.eur_min, filter_data.eur_max)

    currencies = await CurrencyRateDAO.find_by_purchase_range(
        usd_buy_min=filter_data.usd_min,
        usd_buy_max=filter_data.usd_max,
        eur_buy_min=filter_data.eur_min,
        eur_buy_max=filter_data.eur_max,
        session=session
    )

    if not currencies:
        raise HTTPException(status_code=404, detail=settings.ERROR_MESSAGES["not_found"])
    return currencies


@router.post("/currency_in_sale_range/")
async def get_currency_in_sale_range(
        filter_data: CurrencySaleRangeFilterSchema,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> List[CurrencyRateSchema]:
    """Возвращает курсы валют, находящиеся в заданном диапазоне цен продажи для USD и EUR."""
    validate_range(filter_data.usd_sale_min, filter_data.usd_sale_max)
    validate_range(filter_data.eur_sale_min, filter_data.eur_sale_max)

    currencies = await CurrencyRateDAO.find_by_sale_range(
        usd_sell_min=filter_data.usd_sale_min,
        usd_sell_max=filter_data.usd_sale_max,
        eur_sell_min=filter_data.eur_sale_min,
        eur_sell_max=filter_data.eur_sale_max,
        session=session
    )

    if not currencies:
        raise HTTPException(status_code=404, detail=settings.ERROR_MESSAGES["not_found"])
    return currencies


@router.get("/best_purchase_rate/{currency_type}")
async def get_best_purchase_rate(
        currency_type: str,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> BestRateResponse:
    """Возвращает информацию о банках с лучшим курсом покупки для выбранной валюты."""
    currency_type = validate_currency_type(currency_type)
    result = await CurrencyRateDAO.find_best_purchase_rate(currency_type=currency_type, session=session)
    if not result or not result.banks:
        raise HTTPException(status_code=404, detail=settings.ERROR_MESSAGES["not_found"])
    return result


@router.get("/best_sale_rate/{currency_type}")
async def get_best_sale_rate(
        currency_type: str,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> BestRateResponse:
    """Возвращает информацию о банках с лучшим курсом продажи для выбранной валюты."""
    currency_type = validate_currency_type(currency_type)
    result = await CurrencyRateDAO.find_best_sale_rate(currency_type=currency_type, session=session)
    if not result or not result.banks:
        raise HTTPException(status_code=404, detail=settings.ERROR_MESSAGES["not_found"])
    return result


@router.get("/currency_purchase_range/{currency_type}")
async def get_currency_purchase_range(
        currency_type: str,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> CurrencyRangeFilterSchema:
    """Возвращает минимальные и максимальные цены покупки для обеих валют."""
    currency_type = validate_currency_type(currency_type)
    requested_range, other_range = await get_currency_ranges(currency_type, 'buy', session)

    return CurrencyRangeFilterSchema(
        usd_min=requested_range[0] if currency_type == 'usd' else other_range[0],
        usd_max=requested_range[1] if currency_type == 'usd' else other_range[1],
        eur_min=other_range[0] if currency_type == 'usd' else requested_range[0],
        eur_max=other_range[1] if currency_type == 'usd' else requested_range[1]
    )


@router.get("/currency_sale_range/{currency_type}")
async def get_currency_sale_range(
        currency_type: str,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> CurrencySaleRangeFilterSchema:
    """Возвращает минимальные и максимальные цены продажи для обеих валют."""
    currency_type = validate_currency_type(currency_type)
    requested_range, other_range = await get_currency_ranges(currency_type, 'sell', session)

    return CurrencySaleRangeFilterSchema(
        usd_sale_min=requested_range[0] if currency_type == 'usd' else other_range[0],
        usd_sale_max=requested_range[1] if currency_type == 'usd' else other_range[1],
        eur_sale_min=other_range[0] if currency_type == 'usd' else requested_range[0],
        eur_sale_max=other_range[1] if currency_type == 'usd' else requested_range[1]
    )
