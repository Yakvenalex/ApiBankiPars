from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models import CurrencyRate
from app.api.schemas import CurrencyRateSchema
from app.dao.base import BaseDAO
from loguru import logger


class CurrencyRateDAO(BaseDAO):
    model = CurrencyRate

    @classmethod
    async def _find_by_range(cls, field_name: str, min_value: float, max_value: float, session: AsyncSession) -> List[
        CurrencyRateSchema]:
        """
        Универсальный метод для поиска валютных курсов по диапазону для любого поля (покупка или продажа).

        **Параметры:**
        - **field_name**: Поле, по которому будет осуществляться фильтрация (например, 'usd_buy', 'usd_sell').
        - **min_value**: Минимальное значение для фильтра.
        - **max_value**: Максимальное значение для фильтра.

        **Ответ:**
        - Список объектов `CurrencyRateSchema`, представляющих данные о валютных курсах, соответствующие условиям.
        """
        if min_value > max_value:
            logger.error(
                f"Некорректный диапазон для поля {field_name}. Минимальное значение не может быть больше максимального.")
            raise ValueError("Минимальное значение не может быть больше максимального.")

        try:
            query = select(cls.model).filter(
                getattr(cls.model, field_name) >= min_value,
                getattr(cls.model, field_name) <= max_value
            )
            result = await session.execute(query)
            records = result.scalars().all()

            if not records:
                logger.warning(f"Не найдено записей, соответствующих диапазону для поля {field_name}.")

            return [CurrencyRateSchema.from_orm(record) for record in records]

        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске валютных курсов по полю {field_name}: {e}")
            raise

    @classmethod
    async def find_by_purchase_range(cls, usd_buy_min: float, usd_buy_max: float, eur_buy_min: float,
                                     eur_buy_max: float,
                                     session: AsyncSession) -> List[CurrencyRateSchema]:
        """
        Получение валютных курсов по диапазону покупки для USD и EUR.

        **Параметры:**
        - **usd_buy_min**: Минимальная цена покупки USD.
        - **usd_buy_max**: Максимальная цена покупки USD.
        - **eur_buy_min**: Минимальная цена покупки EUR.
        - **eur_buy_max**: Максимальная цена покупки EUR.

        **Ответ:**
        - Список объектов `CurrencyRateSchema`, представляющих данные о валютных курсах, соответствующие условиям.
        """
        purchase_usd = await cls._find_by_range('usd_buy', usd_buy_min, usd_buy_max, session)
        purchase_eur = await cls._find_by_range('eur_buy', eur_buy_min, eur_buy_max, session)

        # Объединяем результаты для покупки USD и EUR
        return purchase_usd + purchase_eur

    @classmethod
    async def find_by_sale_range(cls, usd_sell_min: float, usd_sell_max: float, eur_sell_min: float,
                                 eur_sell_max: float, session: AsyncSession) -> List[CurrencyRateSchema]:
        """
        Получение валютных курсов по диапазону продажи для USD и EUR.

        **Параметры:**
        - **usd_sell_min**: Минимальная цена продажи USD.
        - **usd_sell_max**: Максимальная цена продажи USD.
        - **eur_sell_min**: Минимальная цена продажи EUR.
        - **eur_sell_max**: Максимальная цена продажи EUR.

        **Ответ:**
        - Список объектов `CurrencyRateSchema`, представляющих данные о валютных курсах, соответствующие условиям.
        """
        sale_usd = await cls._find_by_range('usd_sell', usd_sell_min, usd_sell_max, session)
        sale_eur = await cls._find_by_range('eur_sell', eur_sell_min, eur_sell_max, session)

        # Объединяем результаты для продажи USD и EUR
        return sale_usd + sale_eur

    @classmethod
    async def bulk_update_currency(cls, session: AsyncSession, records: List[BaseModel]) -> int:
        """
        Perform bulk update of records for a specific model.

        Args:
            session (AsyncSession): Database session
            records (List[BaseModel]): List of records to update

        Returns:
            int: Number of records updated
        """
        logger.info(f"Bulk updating records for {cls.model.__name__}")
        try:
            updated_count = 0
            for record in records:
                record_dict = record.model_dump(exclude_unset=True)

                # Validate required fields
                if 'bank_en' not in record_dict:
                    logger.warning("Skipping record: Missing 'bank_en'")
                    continue

                # Prepare update data
                update_data = {k: v for k, v in record_dict.items() if k != 'bank_en'}

                # Validate update data
                if not update_data:
                    logger.warning(f"Skipping record: No updatable fields for bank {record_dict['bank_en']}")
                    continue

                # Construct and execute update statement
                stmt = (
                    update(cls.model)
                    .where(cls.model.bank_en == record_dict['bank_en'])
                    .values(**update_data)
                )
                result = await session.execute(stmt)
                updated_count += result.rowcount

            await session.commit()
            logger.info(f"Updated {updated_count} records")
            return updated_count

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error during bulk update: {e}")
            raise

    @classmethod
    async def get_usd_purchase_range(cls, session: AsyncSession) -> tuple:
        """
        Получение минимального и максимального диапазона покупных цен для USD.
        """
        result = await session.execute(select(cls.model.usd_buy).order_by(cls.model.usd_buy))
        usd_values = result.scalars().all()
        if usd_values:
            return min(usd_values), max(usd_values)
        return 0.0, 0.0  # Возвращаем 0, если данные не найдены

    @classmethod
    async def get_eur_purchase_range(cls, session: AsyncSession) -> tuple:
        """
        Получение минимального и максимального диапазона покупных цен для EUR.
        """
        result = await session.execute(select(cls.model.eur_buy).order_by(cls.model.eur_buy))
        eur_values = result.scalars().all()
        if eur_values:
            return min(eur_values), max(eur_values)
        return 0.0, 0.0  # Возвращаем 0, если данные не найдены

    @classmethod
    async def get_usd_sale_range(cls, session: AsyncSession) -> tuple:
        """
        Получение минимального и максимального диапазона продажных цен для USD.
        """
        result = await session.execute(select(cls.model.usd_sell).order_by(cls.model.usd_sell))
        usd_values = result.scalars().all()
        if usd_values:
            return min(usd_values), max(usd_values)
        return 0.0, 0.0  # Возвращаем 0, если данные не найдены

    @classmethod
    async def get_eur_sale_range(cls, session: AsyncSession) -> tuple:
        """
        Получение минимального и максимального диапазона продажных цен для EUR.
        """
        result = await session.execute(select(cls.model.eur_sell).order_by(cls.model.eur_sell))
        eur_values = result.scalars().all()
        if eur_values:
            return min(eur_values), max(eur_values)
        return 0.0, 0.0  # Возвращаем 0, если данные не найдены
