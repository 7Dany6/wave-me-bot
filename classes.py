from aiogram.dispatcher.filters.state import StatesGroup, State


class Form(StatesGroup):
    name = State()
    surname = State()
    feedback = State()


class Person:
    def __init__(self, id):
        self.id = id
