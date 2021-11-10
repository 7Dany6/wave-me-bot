from main import bot, dp
from aiogram import types

def unpack_geo(geopositions: list):
    return '\n'.join(geopositions)

async def register(id: int):
    await bot.send_message(chat_id=id, text="You've already been registered!")

def throw_buttons():
    keyboards = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_location = types.KeyboardButton("Location", request_location=True)
    button_reject = types.KeyboardButton("I'm OK")
    keyboards.add(button_location, button_reject)
    return keyboards
