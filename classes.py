from aiogram.dispatcher.filters.state import StatesGroup, State


class Form(StatesGroup):
    name = State()
    surname = State()
    feedback = State()
