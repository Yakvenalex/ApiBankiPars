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
    Manages the lifecycle of the application scheduler

    Args:
        app (FastAPI): FastAPI application instance
    """
    try:
        # Start scheduler before application startup
        scheduler.add_job(
            upd_data_to_db,
            trigger=IntervalTrigger(minutes=10),
            id='currency_update_job',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Currency rate update scheduler started")
        yield
    except Exception as e:
        logger.error(f"Scheduler initialization error: {e}")
    finally:
        # Shutdown scheduler during application shutdown
        scheduler.shutdown()
        logger.info("Currency rate update scheduler stopped")


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
