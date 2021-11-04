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
from functions import *

database = SQL(f'{DB_NAME}')

queries = defaultdict(list)
last_geopositions = defaultdict(list)
people_tracking_last_geopositions = defaultdict(list)


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


@dp.message_handler(lambda message: message.text == "Register")
async def register(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Share a contact", request_contact=True)
    keyboard.add(button)
    await bot.send_message(chat_id=message.from_user.id, text="In order to use a bot, please share your contact!", reply_markup=keyboard)
    await Form.register.set()

    @dp.message_handler(content_types=['contact'], state=Form.register)
    async def adding_to_db(message: types.Message, state: FSMContext):
        try:
            if str(message.contact['phone number']).startswith('+'):
                database.register(f"@{message.from_user.username}", message.from_user.first_name, message.from_user.id, message.contact['phone_number'][1::])
            else:
                database.register(f"@{message.from_user.username}", message.from_user.first_name, message.from_user.id, message.contact['phone_number'])
            await bot.send_message(chat_id=message.from_user.id, text="Thank you for the registration!")
            await bot.send_message(USER_ID,
                                   text=f"New user: {' '.join([message.from_user.first_name, f'@{message.from_user.username}', message.contact['phone_number']])}")
        except sqlite3.IntegrityError:
            await bot.send_message(chat_id=message.from_user.id, text="You've already been registered!")
        await state.finish()


@dp.message_handler(lambda message: message.text == "Track a person")
async def track_person(message: types.Message):
    await message.answer("Please share a contact of a person (choose from your contacts)!")

    @dp.message_handler(content_types=['contact'])
    async def find_person(message: types.Message):
        print(message.contact['phone_number'])
        if str(message.contact['phone_number']).startswith("+"):
            queries[database.tracked_id(message.contact['phone_number'][1::])[0][0]].append(message.from_user.id)
        else:
            queries[database.tracked_id(message.contact['phone_number'][1::])].append(message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_location = types.KeyboardButton("Yes", request_location=True)
        button_reject = types.KeyboardButton("No")
        keyboard.add(button_location, button_reject)
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
        last_geopositions[message.from_user.id].append(f"{json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']}")
        print(last_geopositions)
        if len(queries[message.from_user.id]) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button_location = types.KeyboardButton("Yes", request_location=True)
            button_reject = types.KeyboardButton("No")
            keyboard.add(button_location, button_reject)
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
            button_location = types.KeyboardButton("Yes", request_location=True)
            button_reject = types.KeyboardButton("No")
            keyboard.add(button_location, button_reject)
            await bot.send_message(message.from_user.id,
                                   text=f"User {database.get_name(queries[message.from_user.id][-1])[0][0]} @{database.get_username(queries[message.from_user.id][-1])[0][0]} with number {database.get_contact(queries[message.from_user.id][-1])[0][0]} wants to track you, are you agree?",
                                   reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Look at last geopositions")
async def peek_at_geoposition(message: types.Message):
    await Form.last_geo.set()
    await message.answer(text="Please share a contact of a person (choose from your contacts)!")

    @dp.message_handler(content_types=['contact'], state=Form.last_geo) # do the same with number.startswith
    async def send_a_request(message: types.Message, state: FSMContext):
        print(message.contact['phone_number'])
        if str(message.contact['phone_number']).startswith("+"):
            people_tracking_last_geopositions[database.tracked_id(message.contact['phone_number'][1::])[0][0]].append(message.from_user.id)
        else:
            people_tracking_last_geopositions[database.tracked_id(message.contact['phone_number'])[0][0]].append(message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(*buttons_for_last_geopositions)
        await bot.send_message(chat_id=database.tracked_id(message.contact['phone_number'][1::])[0][0],
                         text=f"User {message.from_user.first_name} @{message.from_user.username} with number {database.get_contact(message.from_user.id)[0][0]} wants to peek at your last geopositions, are you agree?",
                         reply_markup=keyboard)
        await state.finish()


    @dp.message_handler(lambda message: message.text == "Yep")
    async def send_last_geopositions(message: types.Message):
        if len(last_geopositions[message.from_user.id]) == 0:
            await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                                   text=f'User {database.get_name(message.from_user.id)[0][0]} {database.get_username(message.from_user.id)[0][0]} with number {database.get_contact(message.from_user.id)[0][0]} has no geopositions!')
        elif len(last_geopositions[message.from_user.id]) >= 5:
            await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                             text=f'Last geopositions of user {database.get_name(message.from_user.id)[0][0]} {database.get_username(message.from_user.id)[0][0]} with number {database.get_contact(message.from_user.id)[0][0]}:\n {unpack_geo(last_geopositions[message.from_user.id][-1:-6])}')
        else:
            await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                             text=f'Last geopositions of user {database.get_name(message.from_user.id)[0][0]} {database.get_username(message.from_user.id)[0][0]} with number {database.get_contact(message.from_user.id)[0][0]}:\n {unpack_geo(last_geopositions[message.from_user.id])}')
        people_tracking_last_geopositions[message.from_user.id].pop()
        if len(people_tracking_last_geopositions[message.from_user.id]) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            keyboard.add(*buttons_for_last_geopositions)
            await bot.send_message(message.from_user.id,
                                   text=f"User {database.get_name(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} @{database.get_username(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} with number {database.get_contact(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} wants to peek at your last geopositions, are you agree?",
                                   reply_markup=keyboard)


    @dp.message_handler(lambda message: message.text == "Nope")
    async def reject_request(message: types.Message):
        await bot.send_message(chat_id=people_tracking_last_geopositions[message.from_user.id][-1],
                         text=f"Unfortunately,user {database.get_name(message.from_user.id)[0][0]} {database.get_username(message.from_user.id)[0][0]} with number {database.get_contact(message.from_user.id)[0][0]} rejected your request!")
        people_tracking_last_geopositions[message.from_user.id].pop()
        if len(people_tracking_last_geopositions[message.from_user.id]) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            keyboard.add(*buttons_for_last_geopositions)
            await bot.send_message(message.from_user.id,
                                   text=f"User {database.get_name(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} @{database.get_username(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} with number {database.get_contact(people_tracking_last_geopositions[message.from_user.id][-1])[0][0]} wants to peek at your last geopositions, are you agree?",
                                   reply_markup=keyboard)
