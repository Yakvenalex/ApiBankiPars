from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.auth.router import router as router_auth
from app.api.router import router as router_api
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.scheduler.scheduller import upd_data_to_db

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом планировщика приложения

    Args:
        app (FastAPI): Экземпляр приложения FastAPI
    """
    try:
        # Настройка и запуск планировщика
        scheduler.add_job(
            upd_data_to_db,
            trigger=IntervalTrigger(minutes=10),
            id='currency_update_job',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Планировщик обновления курсов валют запущен")
        yield
    except Exception as e:
        logger.error(f"Ошибка инициализации планировщика: {e}")
    finally:
        # Завершение работы планировщика
        scheduler.shutdown()
        logger.info("Планировщик обновления курсов валют остановлен")


app = FastAPI(lifespan=lifespan)

# Добавляем middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

app.mount('/static', StaticFiles(directory='app/static'), name='static')


@app.get("/")
def home_page():
    return {
        "message": "Добро пожаловать! Пусть эта заготовка станет удобным инструментом для вашей работы и "
                   "приносит вам пользу!"
    }


app.include_router(router_auth)
app.include_router(router_api)
