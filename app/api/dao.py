from pydantic import BaseModel
from sqlalchemy import select, update, desc
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models import CurrencyRate
from app.api.schemas import CurrencyRateSchema, BestRateResponse
from app.config import settings
from app.dao.base import BaseDAO
from loguru import logger


class CurrencyRateDAO(BaseDAO):
    model = CurrencyRate

    @classmethod
    async def _get_value_range(cls, session: AsyncSession, field: str) -> Tuple[float, float]:
        """Получает минимальное и максимальное значение для указанного поля."""
        try:
            result = await session.execute(select(getattr(cls.model, field)))
            values = result.scalars().all()
            return (min(values), max(values)) if values else (0.0, 0.0)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении диапазона для {field}: {e}")
            raise

    @classmethod
    async def _find_by_range(
            cls,
            field_name: str,
            min_value: float,
            max_value: float,
            session: AsyncSession
    ) -> List[CurrencyRateSchema]:
        """Поиск валютных курсов по диапазону для указанного поля."""
        try:
            query = select(cls.model).filter(
                getattr(cls.model, field_name).between(min_value, max_value)
            )
            result = await session.execute(query)
            records = result.scalars().all()
            return [CurrencyRateSchema.from_orm(record) for record in records]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске по диапазону {field_name}: {e}")
            raise

    @classmethod
    async def find_by_range_multi(
            cls,
            ranges: Dict[str, Tuple[float, float]],
            session: AsyncSession
    ) -> List[CurrencyRateSchema]:
        """Поиск валютных курсов по нескольким диапазонам."""
        results = []
        for field, (min_val, max_val) in ranges.items():
            results.extend(await cls._find_by_range(field, min_val, max_val, session))
        return results

    @classmethod
    async def find_by_purchase_range(
            cls,
            usd_buy_min: float,
            usd_buy_max: float,
            eur_buy_min: float,
            eur_buy_max: float,
            session: AsyncSession
    ) -> List[CurrencyRateSchema]:
        """Поиск курсов по диапазону покупки USD/EUR."""
        ranges = {
            'usd_buy': (usd_buy_min, usd_buy_max),
            'eur_buy': (eur_buy_min, eur_buy_max)
        }
        return await cls.find_by_range_multi(ranges, session)

    @classmethod
    async def find_by_sale_range(
            cls,
            usd_sell_min: float,
            usd_sell_max: float,
            eur_sell_min: float,
            eur_sell_max: float,
            session: AsyncSession
    ) -> List[CurrencyRateSchema]:
        """Поиск курсов по диапазону продажи USD/EUR."""
        ranges = {
            'usd_sell': (usd_sell_min, usd_sell_max),
            'eur_sell': (eur_sell_min, eur_sell_max)
        }
        return await cls.find_by_range_multi(ranges, session)

    @classmethod
    async def get_currency_range(cls, currency: str, operation: str, session: AsyncSession) -> Tuple[float, float]:
        """Получает диапазон цен для указанной валюты и операции."""
        field = settings.CURRENCY_FIELDS[currency][operation]
        return await cls._get_value_range(session, field)

    @classmethod
    async def bulk_update_currency(cls, session: AsyncSession, records: List[BaseModel]) -> int:
        """Массовое обновление валютных курсов."""
        try:
            updated_count = 0
            for record in records:
                record_dict = record.model_dump(exclude_unset=True)
                if not (bank_en := record_dict.get('bank_en')):
                    logger.warning("Пропуск записи: отсутствует bank_en")
                    continue

                update_data = {k: v for k, v in record_dict.items() if k != 'bank_en'}
                if not update_data:
                    logger.warning(f"Пропуск записи: нет данных для обновления банка {bank_en}")
                    continue

                stmt = update(cls.model).where(cls.model.bank_en == bank_en).values(**update_data)
                result = await session.execute(stmt)
                updated_count += result.rowcount

            await session.commit()
            logger.info(f"Обновлено записей: {updated_count}")
            return updated_count
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка массового обновления: {e}")
            raise

    @classmethod
    async def _find_best_rate(
            cls,
            currency_type: str,
            operation: str,
            session: AsyncSession
    ) -> Optional[BestRateResponse]:
        """Находит лучший курс для указанной валюты и операции."""
        try:
            field = settings.CURRENCY_FIELDS[currency_type][operation]
            order_by = desc(field) if operation == 'sell' else field

            query = select(cls.model).order_by(order_by)
            result = await session.execute(query)
            rates = result.scalars().all()

            if not rates:
                return None

            best_value = getattr(rates[0], field)
            best_banks = [
                bank.bank_name for bank in rates
                if getattr(bank, field) == best_value
            ]

            return BestRateResponse(rate=best_value, banks=best_banks)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка поиска лучшего курса: {e}")
            raise

    @classmethod
    async def find_best_purchase_rate(cls, currency_type: str, session: AsyncSession) -> Optional[BestRateResponse]:
        """Находит лучший курс покупки для указанной валюты."""
        return await cls._find_best_rate(currency_type, 'buy', session)

    @classmethod
    async def find_best_sale_rate(cls, currency_type: str, session: AsyncSession) -> Optional[BestRateResponse]:
        """Находит лучший курс продажи для указанной валюты."""
        return await cls._find_best_rate(currency_type, 'sell', session)
