import logging
import sqlite3

import requests
from collections import defaultdict

from aiogram.dispatcher import FSMContext
from config import API_KEY, USER_ID, DB_NAME

from main import bot, dp

from aiogram import types
from keyboard import *

from classes import Form
from sql import SQL
database = SQL(f'{DB_NAME}')

queries = defaultdict(list)


@dp.message_handler(commands="start")
async def intro_function(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*buttons)
    await message.answer(f"Welcome, {message.from_user.first_name}! Choose your action:\n\nRemember to switch on Location for correct usage!"
                         , reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Delete an account")
async def delete_acc(message: types.Message):
    database.delete_account(message.from_user.id)
    await bot.send_message(chat_id=message.from_user.id, text="You've successfully deleted your account, hope you'll come back!")

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


@dp.message_handler(lambda message: message.text == "Look at last geopositions")
async def peek_at_geoposition(message: types.Message):
    text = 'https://yandex.ru/'
    await message.answer(text=text)


@dp.message_handler(lambda message: message.text == "Register")
async def register(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Share a contact", request_contact=True)
    keyboard.add(button)
    await bot.send_message(chat_id=message.from_user.id, text="In order to use a bot, please share your contact!", reply_markup=keyboard)

    @dp.message_handler(content_types=['contact'])
    async def adding_to_db(message: types.Message):
        try:
            database.register(f"@{message.from_user.username}", message.from_user.first_name, message.from_user.id, message.contact['phone_number'])
            await bot.send_message(chat_id=message.from_user.id, text="Thank you for the registration!")
            await bot.send_message(USER_ID,
                                   text=f"New user: {' '.join([message.from_user.first_name, f'@{message.from_user.username}', message.contact['phone_number']])}")
        except sqlite3.IntegrityError:
            await bot.send_message(chat_id=message.from_user.id, text="You've already been registered!")


@dp.message_handler(lambda message: message.text == "Track a person")
async def track_person(message: types.Message):
    await message.answer("Please enter phone number of a person (choose from your contacts)")

    @dp.message_handler(content_types=['contact'])
    async def find_person(message: types.Message):
        print(message.contact['phone_number'][1::])
        queries[database.tracked_id(message.contact['phone_number'][1::])[0][0]].append(message.from_user.id)
        print(queries)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton("Yes", request_location=True)
        button2 = types.KeyboardButton("No")
        keyboard.add(button1, button2)
        await bot.send_message(database.tracked_id(message.contact['phone_number'][1::])[0][0],
                               text=f"User {message.from_user.first_name} @{message.from_user.username} with number {database.get_contact(message.from_user.id)[0][0]} wants to track you, are you agree?",
                               reply_markup=keyboard)



    @dp.message_handler(content_types=["location"])
    async def give_position(message: types.Message):
        result = requests.get(url=f'https://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={message["location"]["longitude"]},{message["location"]["latitude"]}&format=json&lang=ru_RU')
        json_data = result.json()
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=f"User {message.from_user.first_name} @{message.from_user.username} with number {database.get_contact(message.from_user.id)[0][0]} is here:\n {json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']}")
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=' '.join([str(message['location']['latitude']), str(message['location']['longitude'])]))
        queries[message.from_user.id].pop()
        if len(queries[message.from_user.id]) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button1 = types.KeyboardButton("Yes", request_location=True)
            button2 = types.KeyboardButton("No", request_contact=True)
            keyboard.add(button1, button2)
            await bot.send_message(message.from_user.id,
                                   text=f"User {database.get_name(queries[message.from_user.id][-1])[0][0]} @{database.get_username(queries[message.from_user.id][-1])[0][0]} with number {database.get_contact(queries[message.from_user.id][-1])[0][0]} wants to track you, are you agree?",
                                   reply_markup=keyboard)


    @dp.message_handler(lambda message: message.text == "No")
    async def give_contact(message: types.Message):
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=f"Unfortunately,user {database.get_name(message.from_user.id)[0][0]} {database.get_username(message.from_user.id)[0][0]} with number {database.get_contact(message.from_user.id)[0][0]} rejected your request, try to make a call!")
        queries[message.from_user.id].pop()
        if len(queries[message.from_user.id]) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button1 = types.KeyboardButton("Yes", request_location=True)
            button2 = types.KeyboardButton("No")
            keyboard.add(button1, button2)
            await bot.send_message(message.from_user.id,
                                   text=f"User {database.get_name(queries[message.from_user.id][-1])[0][0]} @{database.get_username(queries[message.from_user.id][-1])[0][0]} with number {database.get_contact(queries[message.from_user.id][-1])[0][0]} wants to track you, are you agree?",
                                   reply_markup=keyboard)
