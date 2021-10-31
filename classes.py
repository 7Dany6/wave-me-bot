from aiogram.dispatcher.filters.state import StatesGroup, State


class Form(StatesGroup):
    feedback = State()
    last_geo = State()
