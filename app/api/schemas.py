from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BankNameSchema(BaseModel):
    bank_en: str  # Название банка на английском


class CurrencyRateSchema(BankNameSchema):
    bank_name: str  # Название банка на русском
    link: str  # Ссылка на страницу с курсами валют
    usd_buy: float  # Курс покупки USD
    usd_sell: float  # Курс продажи USD
    eur_buy: float  # Курс покупки EUR
    eur_sell: float  # Курс продажи EUR
    update_time: str  # Время последнего обновления

    model_config = ConfigDict(from_attributes=True)


class AdminCurrencySchema(CurrencyRateSchema):
    id: int
    created_at: datetime
    updated_at: datetime


class CurrencyRangeFilterSchema(BaseModel):
    usd_min: float | None = 0
    usd_max: float | None = 0
    eur_min: float | None = 0
    eur_max: float | None = 0


class CurrencySaleRangeFilterSchema(BaseModel):
    usd_sale_min: float | None = 0
    usd_sale_max: float | None = 0
    eur_sale_min: float | None = 0
    eur_sale_max: float | None = 0
