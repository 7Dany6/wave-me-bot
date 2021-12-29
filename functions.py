from aiogram.dispatcher.filters import state
from aiogram.dispatcher import FSMContext

from main import bot, dp
from aiogram import types
from aiogram.types import ParseMode
from language_middleware import i18n
from sql import SQL
from config import DB_NAME

dp.middleware.setup(i18n)
_ = i18n.gettext

database = SQL(f'{DB_NAME}')

def unpack_geo(geopositions: list):
    return '\n'.join(geopositions)

async def register(id: int):
    await bot.send_message(chat_id=id, text=_("You've already been registered!"))

def throw_buttons():
    keyboards = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_location = types.KeyboardButton(_("Here I Am"), request_location=True)
    button_victory = types.KeyboardButton(_("Everything is great{0}").format("\u270C"))
    button_snowflake = types.KeyboardButton(_("Let it snow{0}").format("\u2744"))
    button_cold = types.KeyboardButton(_("Freezing{0}").format("\U0001F976"))
    button_snowman = types.KeyboardButton(_("Happy New Year{0}!").format("\u2603"))
    button_fire = types.KeyboardButton(_("I'm on fire{0}").format("\U0001F525"))
    keyboards.add(button_location, button_victory, button_snowflake, button_cold, button_fire, button_snowman)
    return keyboards

async def send_request(ids: int, first_name: str, message_id:int, contact):
    await bot.send_message(ids,
                           text=_("User [{0}](tg://user?id={1}) with number {2} waves {3} to you\.\n*Switch on your location before answer 'Here I Am'*\.").format(first_name, message_id, contact, '\u270B'),
                           reply_markup=throw_buttons(),
                           parse_mode=ParseMode.MARKDOWN_V2)

def button_contact():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton(_("Share a contact"), request_contact=True)
    keyboard.add(button)
    return keyboard

async def aware_of_contact(id: int):
    await bot.send_message(chat_id=id, text=_('In order to use a bot please share your contact!')
                          , reply_markup=button_contact())

async def thank(id: int):
    await bot.send_message(chat_id=id,
                           text=_("Thank you for the registration!"))

async def action_after_registration(id: int, first_name: str):
    await bot.send_message(id,
                           text=_("Welcome, {0}!\nYou can find instruction in menu!\nPlease, choose your further action from menu!").format(
                               first_name),
                           )

async def cancel(id: int):
    await bot.send_message(id, text=_("Your action has been cancelled"))


async def share_a_contact(id: int):
    await bot.send_message(id,
                           text=_("Please share a contact of a person (choose from your contacts)!"))

async def request_acceptance(id: int):
    await bot.send_message(id,
                           text=_(
                               "Your request has been accepted!\nA person will share his location or state soon, meanwhile you can continue using a bot!"))

async def forwarding(id: int):
    await bot.send_message(id,
                           text=_("Unfortunately, this user has not been registered yet, tell him/her about this bot by forwarding the following message:"))


async def send_request_live(ids: int, first_name: str, message_id:int, contact):
    await bot.send_message(ids,
                           text=_("User [{0}](tg://user?id={1}) with number {2} wants to track your *live* location\.\n*Switch on your location before answer 'Location'*\.").format(first_name, message_id, contact),
                           reply_markup=throw_buttons(),
                           parse_mode=ParseMode.MARKDOWN_V2)