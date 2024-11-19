from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BankNameSchema(BaseModel):
    bank_en: str


class CurrencyRateSchema(BankNameSchema):
    bank_name: str
    link: str
    usd_buy: float
    usd_sell: float
    eur_buy: float
    eur_sell: float
    update_time: str

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


class BestRateResponse(BaseModel):
    rate: float
    banks: list[str]
