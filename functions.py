from main import bot
from aiogram import types
from aiogram.types import ParseMode

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

async def send_request(ids: int, first_name: str, message_id:int, contact):
    await bot.send_message(ids,
                           text=f"User [{first_name}](tg://user?id={message_id}) with number {contact} wants to know how are you\.\n*Switch on your location before answer 'Location'*\.",
                           reply_markup=throw_buttons(),
                           parse_mode=ParseMode.MARKDOWN_V2)