import logging
import sqlite3

import requests
from collections import defaultdict

from aiogram.dispatcher import FSMContext
from config import API_KEY, USER_ID, DB_NAME

from main import bot, dp

from aiogram import types
from keyboard import *

from classes import Form, Person
from sql import SQL
database = SQL(f'{DB_NAME}')

queries = defaultdict(list)


@dp.message_handler(commands="start")
async def intro_function(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*buttons)
    await message.answer(f"Willkommen, {message.from_user.first_name}! Choose your action:\n\nRemember to switch on Location for correct usage!"
                         , reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Cancel", state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info('Cancelling state {}'.format(current_state))
    await state.finish()
    await message.answer('Your action has been cancelled')


@dp.message_handler(lambda message: message.text == "Feedback")
async def feedback(message: types.Message):
    await Form.feedback.set()
    await message.answer("Leave your opinion, it will improve the bot!")


@dp.message_handler(state=Form.feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['feedback'] = message.text
        await bot.send_message(USER_ID,
                               text=f"Feedback from @{message.from_user.username}: {data['feedback']}")
    await state.finish()


@dp.message_handler(lambda message: message.text == "Information")
async def registration(message: types.Message):
    text = 'https://yandex.ru/'
    await message.answer(text=text)


@dp.message_handler(lambda message: message.text == "Register")
async def registration(message: types.Message):
    await Form.name.set()
    await message.answer('What is your name?')


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('What is your surname?')
    await Form.next()


@dp.message_handler(state=Form.surname)
async def process_surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['surname'] = message.text
        try:
            database.register(f"@{message.from_user.username}", data['name'], data['surname'], message.from_user.id) # contact
            await message.answer('Thank you for the registration!')
            await bot.send_message(USER_ID,
                                   text=f"New user: {' '.join([data['name'], data['surname'], f'@{message.from_user.username}'])}")
        except sqlite3.IntegrityError:
            await message.answer("You've already been registered!")
    await state.finish()


@dp.message_handler(lambda message: message.text == "Track a person")
async def track_person(message: types.Message):
    await message.answer("Please enter username of a person (with @ symbol)")

@dp.message_handler()
async def find_person(message: types.Message):
    try:
        assert '@' in message.text
        queries[database.tracked_id(message.text)[0][0]].append(message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton("Yes", request_location=True)
        button2 = types.KeyboardButton("No", request_contact=True)
        keyboard.add(button1, button2)
        await bot.send_message(database.tracked_id(message.text)[0][0],
                               text=f"User @{message.from_user.username} wants to track you, are you agree?",
                               reply_markup=keyboard)
    except AssertionError:
        await bot.send_message(message.from_user.id, text="Please enter username WITH '@'")



    @dp.message_handler(content_types=["location"])
    async def give_position(message: types.Message):
        result = requests.get(url=f'https://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={message["location"]["longitude"]},{message["location"]["latitude"]}&format=json&lang=ru_RU')
        json_data = result.json()
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text'])
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=' '.join([str(message['location']['latitude']), str(message['location']['longitude'])]))
        queries[message.from_user.id].pop()

    @dp.message_handler(content_types=["contact"])
    async def give_contact(message: types.Message):
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=f"Unfortunately, your request has been rejected but you can call {message['contact']['phone_number']}")
        queries[message.from_user.id].pop()
