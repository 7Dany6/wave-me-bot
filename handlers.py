import asyncio
import logging
import sqlite3

import requests
from collections import defaultdict

from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode

from config import API_KEY, USER_ID, DB_NAME

from main import bot, dp

from aiogram import types
from keyboard import *

from classes import Form
from sql import SQL
from functions import *

database = SQL(f'{DB_NAME}')

queries = defaultdict(list)
last_geopositions = defaultdict(list)
people_tracking_last_geopositions = defaultdict(list)


@dp.message_handler(commands="start")
async def intro_function(message):
    if database.user_exists(message.from_user.id):
        await register(message.from_user.id)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton("Share a contact", request_contact=True)
        keyboard.add(button)
        await bot.send_message(chat_id=message.from_user.id, text='In order to use a bot please share your contact!'
                             , reply_markup=keyboard)
        await Form.register.set()


    @dp.message_handler(content_types=['contact'], state=Form.register)
    async def adding_to_db(message: types.Message, state: FSMContext):
        try:
            if str(message.contact['phone_number']).startswith('+'):
                database.register(message.from_user.first_name, message.from_user.id, message.contact['phone_number'][1::])
            else:
                database.register(message.from_user.first_name, message.from_user.id, message.contact['phone_number'])
            await bot.send_message(chat_id=message.from_user.id, text="Thank you for the registration!")
            await bot.send_message(USER_ID,
                                   text=f"New user: {' '.join([message.from_user.first_name, f'@{message.from_user.username}', message.contact['phone_number']])}")
        except sqlite3.IntegrityError:
            await register(message.from_user.id)
        await bot.send_message(message.from_user.id,
                               text=f'Welcome, {message.from_user.first_name}! \nPlease, choose your further action from menu!',
                               )
        await state.finish()


@dp.message_handler(commands="cancel", state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info('Cancelling state {}'.format(current_state))
    await state.finish()
    await message.answer('Your action has been cancelled')


@dp.message_handler(commands="feedback")
async def feedback(message: types.Message):
    await Form.feedback.set()
    await message.answer("Leave your opinion, it will improve the bot!")


@dp.message_handler(state=Form.feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['feedback'] = message.text
        await bot.send_message(USER_ID,
                               text=f"Feedback from [{message.from_user.first_name}](tg://user?id={message.from_user.id}): {data['feedback']}",
                               parse_mode=ParseMode.MARKDOWN_V2)
    await state.finish()


@dp.message_handler(commands="care")
async def track_person(message: types.Message):
    if database.tracking_existance(message.from_user.id):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons_for_tracking = [database.get_first_name(contact[0])[0][0] for contact in database.get_trackable(message.from_user.id)]
        keyboard.add(*buttons_for_tracking)
        await bot.send_message(message.from_user.id,
                               text="Please share a contact of a person (choose from your contacts) or click a button with his/her name!",
                               reply_markup=keyboard)
    else:
        await bot.send_message(message.from_user.id,
                               text="Please share a contact of a person (choose from your contacts)!")
    await Form.tracking.set()

    @dp.message_handler(content_types=['contact', 'text'], state=Form.tracking)
    async def find_person(message: types.Message, state: FSMContext):
        await bot.send_message(message.from_user.id,
                               text="Your request has been accepted!\nA person will share his location or state soon, meanwhile you can continue using a bot!")
        try:
            if message.content_type == 'text':
                queries[database.tracked_id(database.get_contact_check(message.from_user.id, message.text)[0][0])[0][0]].append(message.from_user.id)
            else:
                if str(message.contact['phone_number']).startswith("+"):
                    print("here i am")
                    queries[database.tracked_id(message.contact['phone_number'][1::])[0][0]].append(message.from_user.id)
                    print(queries)
                elif "+" not in str(message.contact['phone_number']):
                    print("i'm here")
                    queries[database.tracked_id(message.contact['phone_number'])[0][0]].append(message.from_user.id)
            keyboards = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # duplication_buttons2
            button_location = types.KeyboardButton("Location", request_location=True)
            button_reject = types.KeyboardButton("I'm OK")
            keyboards.add(button_location, button_reject)
            if message.content_type == 'contact':
                if str(message.contact['phone_number']).startswith("+"):
                    await bot.send_message(database.tracked_id(message.contact['phone_number'][1::])[0][0],
                                           text=f"User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} wants to know how are you\.\n*Switch on your location before answer 'Location'*\.",  # duplication except 1st line
                                           reply_markup=keyboards,
                                           parse_mode=ParseMode.MARKDOWN_V2)
                elif "+" not in str(message.contact['phone_number']):
                    await bot.send_message(database.tracked_id(message.contact['phone_number'])[0][0],
                                           text=f"User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} wants to know how are you\.\n*Switch on your location before answer 'Location'*\.",
                                           reply_markup=keyboards,
                                           parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await bot.send_message(database.tracked_id(database.get_contact_check(message.from_user.id, message.text)[0][0])[0][0],
                                       text=f"User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} wants to know how are you\.\n*Switch on your location before answer 'Location'*\.",
                                       reply_markup=keyboards,
                                       parse_mode=ParseMode.MARKDOWN_V2)
        except IndexError:
            await bot.send_message(message.from_user.id, text="Unfortunately, this user has not been registered yet, tell him/her about this bot by forwarding the following message:")
            await bot.send_message(message.from_user.id, text='@here_i_ambot')
        await state.finish()


    @dp.message_handler(content_types=["location"])
    async def give_position(message: types.Message):
        result = requests.get(url=f'https://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={message["location"]["longitude"]},{message["location"]["latitude"]}&format=json&lang=ru_RU')
        json_data = result.json()
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=f"User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} is here:\n{json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']}",
                               parse_mode=ParseMode.MARKDOWN_V2)
        await bot.send_location(queries[message.from_user.id][-1], latitude=message['location']['latitude'],
                                longitude=message['location']['longitude'])
        if not database.user_existance(queries[message.from_user.id][-1], message.from_user.id):
            database.add_to_tracking_trackable(queries[message.from_user.id][-1], database.get_contact(queries[message.from_user.id][-1])[0][0],
                                               message.from_user.id, database.get_contact(message.from_user.id)[0][0], database.get_name(message.from_user.id)[0][0])
        else:
            database.increase_counter(database.get_contact(queries[message.from_user.id][-1])[0][0], database.get_contact(message.from_user.id)[0][0])
        queries[message.from_user.id].pop()
        last_geopositions[message.from_user.id].append(f"{json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']}")  # база с координатами, временем, contact и кто просил
        if len(queries[message.from_user.id]) != 0:  # duplication block
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # duplication_buttons2
            button_location = types.KeyboardButton("Location", request_location=True)
            button_reject = types.KeyboardButton("I'm OK")
            keyboard.add(button_location, button_reject)
            await bot.send_message(message.from_user.id,
                                   text=f"User [{database.get_name(queries[message.from_user.id][-1])[0][0]}](tg://user?id={queries[message.from_user.id][-1]}) with number {database.get_contact(queries[message.from_user.id][-1])[0][0]} wants to know how are you\.\n*Switch on your location before answer 'Location'*\.",  # duplication buttons except 1st line
                                   reply_markup=keyboard,
                                   parse_mode=ParseMode.MARKDOWN_V2)



    @dp.message_handler(lambda message: message.text == "I'm OK")
    async def give_contact(message: types.Message):
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=f"User [{database.get_name(message.from_user.id)[0][0]}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} feels OK\!", parse_mode=ParseMode.MARKDOWN_V2)
        queries[message.from_user.id].pop()
        if len(queries[message.from_user.id]) != 0:  # duplication block
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # duplication_buttons2
            button_location = types.KeyboardButton("Location", request_location=True)
            button_reject = types.KeyboardButton("I'm OK")
            keyboard.add(button_location, button_reject)
            await bot.send_message(message.from_user.id,
                                   text=f"User [{database.get_name(queries[message.from_user.id][-1])[0][0]}](tg://user?id={queries[message.from_user.id][-1]}) with number {database.get_contact(queries[message.from_user.id][-1])[0][0]} wants to know how are you\.\n*Switch on your location before answer 'Location'*\.",
                                   reply_markup=keyboard,
                                   parse_mode=ParseMode.MARKDOWN_V2)







@dp.message_handler(commands="last_geo")
async def peek_at_geoposition(message: types.Message):
    if database.tracking_existance(message.from_user.id):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        #print([contact[0] for contact in database.get_trackable(message.from_user.id)])
        #print([database.get_first_name(contact[0]) for contact in database.get_trackable(message.from_user.id)])
        buttons_for_tracking = [database.get_first_name(contact[0])[0][0] for contact in database.get_trackable(message.from_user.id)]
        keyboard.add(*buttons_for_tracking)
        await bot.send_message(message.from_user.id,
                               text="Please share a contact of a person (choose from your contacts) or click a button with his/her name!",
                               reply_markup=keyboard)
    else:
        await bot.send_message(message.from_user.id,
                               text="Please share a contact of a person (choose from your contacts)!")
    await Form.last_geo.set()


    @dp.message_handler(content_types=['contact', 'text'], state=Form.last_geo)
    async def send_a_request(message: types.Message, state: FSMContext):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        try:
            if message.content_type == 'text':
                people_tracking_last_geopositions[database.tracked_id(database.get_contact_check(message.from_user.id, message.text)[0][0])[0][0]].append(message.from_user.id)
            else:
                if str(message.contact['phone_number']).startswith("+"):
                    people_tracking_last_geopositions[database.tracked_id(message.contact['phone_number'][1::])[0][0]].append(message.from_user.id)
                elif "+" not in str(message.contact['phone_number']):
                    people_tracking_last_geopositions[database.tracked_id(message.contact['phone_number'])[0][0]].append(message.from_user.id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            keyboard.add(*buttons_for_last_geopositions)
            if message.content_type == 'contact':
                if str(message.contact['phone_number']).startswith("+"):
                    await bot.send_message(chat_id=database.tracked_id(message.contact['phone_number'][1::])[0][0],
                                           text=f"User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} wants to peek at your last geopositions, are you agree?",
                                           reply_markup=keyboard,
                                           parse_mode=ParseMode.MARKDOWN_V2)
                else:
                    await bot.send_message(chat_id=database.tracked_id(message.contact['phone_number'])[0][0],
                                           text=f"User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} wants to peek at your last geopositions, are you agree?",
                                           reply_markup=keyboard,
                                           parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await bot.send_message(chat_id=database.tracked_id(database.get_contact_check(message.from_user.id, message.text)[0][0])[0][0],
                                       text=f"User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} wants to peek at your last geopositions, are you agree?",
                                       reply_markup=keyboard,
                                       parse_mode=ParseMode.MARKDOWN_V2)
        except IndexError:
            await bot.send_message(message.from_user.id,
                                   text="Unfortunately, this user has not been registered yet, tell him/her about this bot!")
        await state.finish()


    @dp.message_handler(lambda message: message.text == "Yep")
    async def send_last_geopositions(message: types.Message):
        if len(last_geopositions[message.from_user.id]) == 0:
            await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                                   text=f'User [{database.get_name(message.from_user.id)[0][0]}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} has no geopositions\! Be the first to track him\!', parse_mode=ParseMode.MARKDOWN_V2)
        elif len(last_geopositions[message.from_user.id]) >= 5:
            await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                             text=f'Last geopositions of user [{database.get_name(message.from_user.id)[0][0]}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]}:\n {unpack_geo(last_geopositions[message.from_user.id][-1:-6])}', parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                             text=f'Last geopositions of user [{database.get_name(message.from_user.id)[0][0]}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]}:\n {unpack_geo(last_geopositions[message.from_user.id])}', parse_mode=ParseMode.MARKDOWN_V2)
        people_tracking_last_geopositions[message.from_user.id].pop()
        if len(people_tracking_last_geopositions[message.from_user.id]) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            keyboard.add(*buttons_for_last_geopositions)
            await bot.send_message(message.from_user.id,
                                   text=f"User [{database.get_name(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]}](tg://user?id={people_tracking_last_geopositions[message.from_user.id][-1]}) with number {database.get_contact(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} wants to peek at your last geopositions, are you agree?",
                                   reply_markup=keyboard,
                                   parse_mode=ParseMode.MARKDOWN_V2)


    @dp.message_handler(lambda message: message.text == "Nope, I'm OK")
    async def reject_request(message: types.Message):
        await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                         text=f"Unfortunately,user [{database.get_name(message.from_user.id)[0][0]}](tg://user?id={message.from_user.id}) with number {database.get_contact(message.from_user.id)[0][0]} rejected your request, but feels OK\!", parse_mode=ParseMode.MARKDOWN_V2)
        people_tracking_last_geopositions[message.from_user.id].pop()
        if len(people_tracking_last_geopositions[message.from_user.id]) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            keyboard.add(*buttons_for_last_geopositions)
            await bot.send_message(message.from_user.id,
                                   text=f"User [{database.get_name(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]}](tg://user?id={people_tracking_last_geopositions[message.from_user.id][-1]}) with number {database.get_contact(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} wants to peek at your last geopositions, are you agree?",
                                   reply_markup=keyboard,
                                   parse_mode=ParseMode.MARKDOWN_V2)


