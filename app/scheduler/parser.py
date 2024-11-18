import aiohttp
import asyncio
from loguru import logger
from bs4 import BeautifulSoup
from aiohttp import ClientSession, ClientTimeout, ClientError
from typing import List, Optional
from pydantic import BaseModel
from app.api.schemas import CurrencyRateSchema


# Асинхронная функция для получения HTML с повторными попытками и экспоненциальной задержкой
async def fetch_html(url: str, session: ClientSession, retries: int = 3) -> Optional[str]:
    attempt = 0
    while attempt < retries:
        try:
            async with session.get(url) as response:
                response.raise_for_status()  # Вызывает исключение при ошибке HTTP
                return await response.text()
        except (ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Ошибка при запросе {url}: {e}")
            attempt += 1
            if attempt == retries:
                logger.critical(f"Не удалось получить данные с {url} после {retries} попыток.")
                return None
            # Экспоненциальная задержка
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Неизвестная ошибка при запросе {url}: {e}")
            return None
    return None


# Функция для извлечения информации о ссылке
def get_link_info(link_draft):
    link = link_draft.get('href') if link_draft else None
    if link:
        return 'https://ru.myfin.by' + link, link.split('/')[2]
    return None, None


# Функция для парсинга таблицы с валютами с дополнительной обработкой ошибок
def parse_currency_table(html: str) -> List[BaseModel]:
    soup = BeautifulSoup(html, 'html.parser')

    try:
        # Находим таблицу с валютными курсами
        table = soup.find('table', class_='content_table').find('tbody')
        rows = table.find_all('tr')
        currencies = []

        # Извлекаем информацию о каждом банке
        for row in rows:
            bank_name = row.find('td', class_='bank_name').get_text(strip=True)
            link = row.find('a')

            try:
                # Преобразуем курсы валют в float
                usd_buy = float(row.find_all('td', class_='USD')[0].get_text(strip=True).replace(',', '.'))
                usd_sell = float(row.find_all('td', class_='USD')[1].get_text(strip=True).replace(',', '.'))
                eur_buy = float(row.find_all('td', class_='EUR')[0].get_text(strip=True).replace(',', '.'))
                eur_sell = float(row.find_all('td', class_='EUR')[1].get_text(strip=True).replace(',', '.'))
            except (ValueError, IndexError) as e:
                logger.warning(f"Ошибка при парсинге курсов валют для {bank_name}: {e}")
                continue  # Пропускаем этот банк, если курс не удалось извлечь

            update_time = row.find('time').get_text(strip=True)
            link_info = get_link_info(link)
            currencies.append(CurrencyRateSchema(**{
                'bank_name': bank_name,
                'bank_en': link_info[1],
                'link': link_info[0],
                'usd_buy': usd_buy,
                'usd_sell': usd_sell,
                'eur_buy': eur_buy,
                'eur_sell': eur_sell,
                'update_time': update_time,
            }))
        return currencies
    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML: {e}")
        return []


# Функция для получения данных с одной страницы
async def fetch_page_data(url: str, session: ClientSession) -> List[BaseModel]:
    html = await fetch_html(url, session)
    if html:
        return parse_currency_table(html)
    return []


# Функция для сбора данных с нескольких страниц асинхронно с обработкой ошибок
async def fetch_all_currencies() -> List[BaseModel]:
    all_currencies = []
    base_url = 'https://ru.myfin.by/currency?page='

    # Создаем сессию с таймаутом
    timeout = ClientTimeout(total=10, connect=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []

        # Создаем асинхронные задачи для получения данных с нескольких страниц
        for page in range(1, 5):
            url = f'{base_url}{page}'
            tasks.append(fetch_page_data(url, session))

        # Дожидаемся выполнения всех задач
        results = await asyncio.gather(*tasks)

        # Обрабатываем полученные данные
        for currencies in results:
            all_currencies.extend(currencies)

    return all_currencies
