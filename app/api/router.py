from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user, get_current_admin_user
from app.auth.models import User
from app.dao.session_maker import SessionDep
from app.api.dao import CurrencyRateDAO

from app.api.schemas import CurrencyRateSchema, BankNameSchema, CurrencyRangeFilterSchema, AdminCurrencySchema, \
    CurrencySaleRangeFilterSchema

router = APIRouter(prefix='/api', tags=['API'])


@router.get("/all_currency/", response_model=List[CurrencyRateSchema], summary="Получить все валютные курсы")
async def get_all_currency(user_data: User = Depends(get_current_user),
                           session: AsyncSession = SessionDep) -> List[CurrencyRateSchema]:
    """
    Получение всех валютных курсов для всех банков.

    **Ответ:**
    - Список объектов `CurrencyRateSchema`, представляющих все валютные курсы.
    """
    return await CurrencyRateDAO.find_all(session=session, filters=None)


@router.get("/all_currency_admin/", response_model=List[AdminCurrencySchema],
            summary="Получить все валютные курсы для админа")
async def get_all_currency_admin(user_data: User = Depends(get_current_admin_user),
                                 session: AsyncSession = SessionDep) -> List[AdminCurrencySchema]:
    """
    Получение всех валютных курсов для всех банков (только для администратора).

    **Ответ:**
    - Список объектов `AdminCurrencySchema`, представляющих все валютные курсы для администраторов.
    """
    return await CurrencyRateDAO.find_all(session=session, filters=None)


@router.get("/currency_by_bank/{bank_en}", response_model=List[CurrencyRateSchema],
            summary="Получить валютные курсы для банка")
async def get_currency_by_bank(bank_en: str, user_data: User = Depends(get_current_user),
                               session: AsyncSession = SessionDep) -> List[CurrencyRateSchema]:
    """
    Получение валютных курсов для указанного банка.

    **Параметры:**
    - **bank_en**: Название банка на английском языке (например, "sberbank").

    **Ответ:**
    - Список объектов `CurrencyRateSchema`, представляющих валютные курсы для указанного банка.

    **Ошибки:**
    - 404 Not Found: Если банк не найден.
    """
    currencies = await CurrencyRateDAO.find_all(session=session, filters=BankNameSchema(bank_en=bank_en))
    if not currencies:
        raise HTTPException(status_code=404, detail="Банк не найден.")
    return currencies


@router.post("/currency_in_purchase_range/", response_model=List[CurrencyRateSchema],
             summary="Получить валютные курсы в диапазоне покупки")
async def get_currency_in_purchase_range(
        filter_data: CurrencyRangeFilterSchema,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> List[CurrencyRateSchema]:
    """
    Получение валютных курсов, где покупка доллара или евро находится в пределах заданного диапазона.

    **Параметры:**
    - **usd_min**: Минимальное значение для покупки USD.
    - **usd_max**: Максимальное значение для покупки USD.
    - **eur_min**: Минимальное значение для покупки EUR.
    - **eur_max**: Максимальное значение для покупки EUR.

    **Ответ:**
    - Список объектов `CurrencyRateSchema`, представляющих данные о валютных курсах, соответствующие условиям.

    **Ошибки:**
    - 400 Bad Request: Если диапазоны заданы некорректно.
    - 404 Not Found: Если не найдено валютных курсов в пределах указанного диапазона.
    """
    # Проверка корректности диапазонов
    if filter_data.usd_min > filter_data.usd_max or filter_data.eur_min > filter_data.eur_max:
        raise HTTPException(status_code=400, detail="Неверно задан диапазон.")

    currencies = await CurrencyRateDAO.find_by_purchase_range(
        usd_buy_min=filter_data.usd_min,
        usd_buy_max=filter_data.usd_max,
        eur_buy_min=filter_data.eur_min,
        eur_buy_max=filter_data.eur_max,
        session=session
    )

    if not currencies:
        raise HTTPException(status_code=404, detail="Не найдено валютных курсов в пределах указанного диапазона.")

    return currencies


@router.post("/currency_in_sale_range/", response_model=List[CurrencyRateSchema],
             summary="Получить валютные курсы в диапазоне продажи")
async def get_currency_in_sale_range(
        filter_data: CurrencySaleRangeFilterSchema,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = SessionDep
) -> List[CurrencyRateSchema]:
    """
    Получение валютных курсов, где продажа доллара или евро находится в пределах заданного диапазона.

    **Параметры:**
    - **usd_sale_min**: Минимальное значение для продажи USD.
    - **usd_sale_max**: Максимальное значение для продажи USD.
    - **eur_sale_min**: Минимальное значение для продажи EUR.
    - **eur_sale_max**: Максимальное значение для продажи EUR.

    **Ответ:**
    - Список объектов `CurrencyRateSchema`, представляющих данные о валютных курсах, соответствующие условиям.

    **Ошибки:**
    - 400 Bad Request: Если диапазоны заданы некорректно.
    - 404 Not Found: Если не найдено валютных курсов в пределах указанного диапазона.
    """
    # Проверка корректности диапазонов
    if filter_data.usd_sale_min > filter_data.usd_sale_max or filter_data.eur_sale_min > filter_data.eur_sale_max:
        raise HTTPException(status_code=400, detail="Неверно задан диапазон.")

    currencies = await CurrencyRateDAO.find_by_sale_range(
        usd_sell_min=filter_data.usd_sale_min,
        usd_sell_max=filter_data.usd_sale_max,
        eur_sell_min=filter_data.eur_sale_min,
        eur_sell_max=filter_data.eur_sale_max,
        session=session
    )

    if not currencies:
        raise HTTPException(status_code=404, detail="Не найдено валютных курсов в пределах указанного диапазона.")

    return currencies


# Метод для получения диапазона покупной цены для указанной валюты (USD или EUR)
@router.get("/currency_purchase_range/{currency_type}", response_model=CurrencyRangeFilterSchema,
            summary="Получить диапазон покупной цены для валюты")
async def get_currency_purchase_range(currency_type: str, user_data: User = Depends(get_current_user),
                                      session: AsyncSession = SessionDep):
    """
    Получение диапазона покупной цены для указанной валюты (USD или EUR).

    **Параметры:**
    - **currency_type**: Тип валюты, для которой нужно получить диапазон покупной цены. Допустимые значения: "usd" или "eur".

    **Ответ:**
    - Объект `CurrencyRangeFilterSchema`, который содержит минимальное и максимальное значение покупной цены для указанной валюты.

    **Ошибки:**
    - 400 Bad Request: Если указана некорректная валюта.
    """
    if currency_type not in ["usd", "eur"]:
        raise HTTPException(status_code=400, detail="Некорректный тип валюты. Используйте 'usd' или 'eur'.")

    # Получаем диапазон покупных цен для выбранной валюты
    if currency_type == "usd":
        min_value, max_value = await CurrencyRateDAO.get_usd_purchase_range(session)
    else:
        min_value, max_value = await CurrencyRateDAO.get_eur_purchase_range(session)

    # Возвращаем диапазон
    return CurrencyRangeFilterSchema(usd_min=min_value, usd_max=max_value, eur_min=min_value, eur_max=max_value)


# Метод для получения диапазона продажной цены для указанной валюты (USD или EUR)
@router.get("/currency_sale_range/{currency_type}", response_model=CurrencySaleRangeFilterSchema,
            summary="Получить диапазон продажной цены для валюты")
async def get_currency_sale_range(currency_type: str, user_data: User = Depends(get_current_user),
                                  session: AsyncSession = SessionDep):
    """
    Получение диапазона продажной цены для указанной валюты (USD или EUR).

    **Параметры:**
    - **currency_type**: Тип валюты, для которой нужно получить диапазон продажной цены. Допустимые значения: "usd" или "eur".

    **Ответ:**
    - Объект `CurrencySaleRangeFilterSchema`, который содержит минимальное и максимальное значение продажной цены для указанной валюты.

    **Ошибки:**
    - 400 Bad Request: Если указана некорректная валюта.
    """
    if currency_type not in ["usd", "eur"]:
        raise HTTPException(status_code=400, detail="Некорректный тип валюты. Используйте 'usd' или 'eur'.")

    # Получаем диапазон продажных цен для выбранной валюты
    if currency_type == "usd":
        min_value, max_value = await CurrencyRateDAO.get_usd_sale_range(session)
    else:
        min_value, max_value = await CurrencyRateDAO.get_eur_sale_range(session)

    # Возвращаем диапазон
    return CurrencySaleRangeFilterSchema(usd_sale_min=min_value, usd_sale_max=max_value,
                                         eur_sale_min=min_value, eur_sale_max=max_value)
