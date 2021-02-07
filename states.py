from aiogram.dispatcher.filters.state import StatesGroup, State


class NewTicket(StatesGroup):
    wf_body = State()
    wf_price = State()
    wf_aff = State()


class NewOffer(StatesGroup):
    wf_body = State()
    wf_price = State()
    wf_aff = State()


class NewPayment(StatesGroup):
    wf_start = State()
    wf_amount = State()
