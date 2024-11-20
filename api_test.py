import aiohttp
from loguru import logger
from asyncio import run

BASE_SITE = 'https://bankiru-yakvenalex.amvera.io'
TAG_AUTH = 'auth'
TAG_API = 'api'
headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
}
USER_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3IiwiZXhwIjoxNzM0Njg2MDM4fQ.Tl_wF1cnTDxLslNkk5VJm_3-2xLcKUEIUX_odldKims'
ADMIN_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzM0Njg3MjY3fQ.NZRMGwTPkT9yPYvcu-6hCg-LDF0QhrcRDIrI8Aas82w'


async def register_user(
        email: str,
        phone_number: str,
        first_name: str,
        last_name: str,
        password: str,
        confirm_password: str
):
    """
    Выполняет POST-запрос на регистрацию пользователя.
    """
    url = f"{BASE_SITE}/{TAG_AUTH}/register/"

    payload = {
        "email": email,
        "phone_number": phone_number,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
        "confirm_password": confirm_password,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                response_data = await response.json()
                logger.info(response_data)
                return response_data
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка запроса: {e}")
            return None


async def login_user(email: str, password: str):
    """
    Выполняет POST-запрос для авторизации пользователя.
    """
    url = f"{BASE_SITE}/{TAG_AUTH}/login/"

    payload = {
        "email": email,
        "password": password,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                response_data = await response.json()
                if response_data:
                    if response_data.get("ok"):
                        logger.success(f"Access token: {response_data['access_token']}")
                    else:
                        logger.warning(f"Ошибка входа: {response_data.get('message')}")
                return response_data
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка запроса: {e}")
            return None


async def get_all_currency(access_token: str, method_name='all_currency'):
    """
    Выполняет запрос для получения всех валют.
    """
    url = f"{BASE_SITE}/{TAG_API}/{method_name}/"
    headers['cookie'] = f"users_access_token={access_token}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response_data = await response.json()
                logger.info(f"Статус: {response.status}")
                return response_data
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            return None


rez = run(get_all_currency(access_token=USER_TOKEN, method_name='all_currency_admin'))
print(rez)
