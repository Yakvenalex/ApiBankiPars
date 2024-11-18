from sqlalchemy.orm import Mapped
from app.dao.database import Base, str_uniq, float_col


class CurrencyRate(Base):
    # Название банка (на русском)
    bank_name: Mapped[str_uniq]

    # Название банка (на английском, например, для поиска)
    bank_en: Mapped[str_uniq]

    # Ссылка на страницу с курсами валют
    link: Mapped[str_uniq]

    # Курсы валют: покупка и продажа USD
    usd_buy: Mapped[float_col]
    usd_sell: Mapped[float_col]

    # Курсы валют: покупка и продажа EUR
    eur_buy: Mapped[float_col]
    eur_sell: Mapped[float_col]

    # Время последнего обновления
    update_time: Mapped[str]
