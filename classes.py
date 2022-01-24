from aiogram.dispatcher.filters.state import StatesGroup, State


class Form(StatesGroup):
    feedback = State()
    register = State()
    last_geo = State()
    tracking = State()
    fav_location = State()