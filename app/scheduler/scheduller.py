from app.api.dao import CurrencyRateDAO
from app.dao.session_maker import session_manager
from app.scheduler.parser import fetch_all_currencies


@session_manager.connection(commit=True)
async def add_data_to_db(session):
    rez = await fetch_all_currencies()
    await CurrencyRateDAO.add_many(session=session, instances=rez)


@session_manager.connection(commit=True)
async def upd_data_to_db(session):
    rez = await fetch_all_currencies()
    await CurrencyRateDAO.bulk_update_currency(session=session, records=rez)
