import asyncio
import logging
import sqlite3

import requests
from collections import defaultdict

from aiogram.dispatcher import FSMContext

from config import API_KEY, USER_ID, DB_NAME
from functions import _

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
        await aware_of_contact(message.from_user.id)
        await Form.register.set()

    @dp.message_handler(content_types=['contact'], state=Form.register)
    async def adding_to_db(message: types.Message, state: FSMContext):
        try:
            if str(message.contact['phone_number']).startswith('+'):
                database.register(message.from_user.first_name,
                                  message.from_user.id,
                                  message.contact['phone_number'][1::])
            else:
                database.register(message.from_user.first_name,
                                  message.from_user.id,
                                  message.contact['phone_number'])
            await thank(message.from_user.id)
            await bot.send_message(USER_ID,
                                   text=f"New user: {' '.join([message.from_user.first_name,f'@{message.from_user.username}', message.contact['phone_number']])}")
        except sqlite3.IntegrityError:
            await register(message.from_user.id)
        await action_after_registration(message.from_user.id,
                                  message.from_user.first_name)
        await state.finish()


@dp.message_handler(commands="cancel", state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info('Cancelling state {}'.format(current_state))
    await state.finish()
    await cancel(message.from_user.id)


@dp.message_handler(commands="feedback", state='*')
async def feedback(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, text=_("Leave your opinion, it will improve the bot!"))
    await Form.feedback.set()


    @dp.message_handler(state=Form.feedback)
    async def process_feedback(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['feedback'] = message.text
            await bot.send_message(USER_ID,
                                   text=f"Feedback from [{message.from_user.first_name}](tg://user?id={message.from_user.id}): {data['feedback']}",
                                   parse_mode=ParseMode.MARKDOWN_V2)
        await state.finish()


@dp.message_handler(commands="care", state='*')
async def track_person(message: types.Message, state: FSMContext):
    if database.tracking_existance(message.from_user.id):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons_for_tracking = [database.get_first_name(contact[0])[0][0] for contact in
                                database.get_trackable(message.from_user.id)]
        keyboard.add(*buttons_for_tracking)
        await bot.send_message(message.from_user.id,
                               text=_(
                                   "Please share a contact of a person (choose from your contacts) or click a button with his/her name!"),
                               reply_markup=keyboard)
    else:
        await share_a_contact(message.from_user.id)
    await Form.tracking.set()

    @dp.message_handler(content_types=['contact', 'text'], state=Form.tracking)
    async def find_person(message: types.Message, state: FSMContext):
	if message.text == _("I'm OK"):
		await give_contact(message=message)
	else:
		await request_acceptance(message.from_user.id)
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
			if message.content_type == 'contact':
				if str(message.contact['phone_number']).startswith("+"):
					await send_request(database.tracked_id(message.contact['phone_number'][1::])[0][0],
							   message.from_user.first_name,
							   message.from_user.id,
							   database.get_contact(message.from_user.id)[0][0])
				elif "+" not in str(message.contact['phone_number']):
					await send_request(database.tracked_id(message.contact['phone_number'])[0][0],
							   message.from_user.first_name,
							   message.from_user.id,
							   database.get_contact(message.from_user.id)[0][0])
			else:
				await send_request(database.tracked_id(database.get_contact_check(message.from_user.id, message.text)[0][0])[0][0],
						   message.from_user.first_name,
						   message.from_user.id,
						   database.get_contact(message.from_user.id)[0][0])
		except IndexError:
			await forwarding(message.from_user.id)
			await bot.send_message(message.from_user.id, text='@here_i_ambot')
		await state.finish()


    @dp.message_handler(content_types=["location"], state="*")
    async def give_position(message: types.Message, state: FSMContext):
        result = requests.get(url=f'https://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={message["location"]["longitude"]},{message["location"]["latitude"]}&format=json&lang=ru_RU')
        json_data = result.json()
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=_("User [{0}](tg://user?id={1}) with number {2} is here:\n{3}").format(message.from_user.first_name, message.from_user.id, database.get_contact(message.from_user.id)[0][0], json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']),
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
        if len(queries[message.from_user.id]) != 0:
            await send_request(message.from_user.id,
                               database.get_name(queries[message.from_user.id][-1])[0][0],
                               queries[message.from_user.id][-1],
                               database.get_contact(queries[message.from_user.id][-1])[0][0])


    @dp.message_handler(content_types=["text"], state="*")
    async def give_contact(message: types.Message, state: FSMContext):
        await bot.send_message(chat_id=queries[message.from_user.id][-1],
                               text=_("User [{0}](tg://user?id={1}) with number {2} feels OK\!").format(database.get_name(message.from_user.id)[0][0], message.from_user.id, database.get_contact(message.from_user.id)[0][0])
                               , parse_mode=ParseMode.MARKDOWN_V2)
        queries[message.from_user.id].pop()
        if len(queries[message.from_user.id]) != 0:
            await send_request(message.from_user.id,
                         database.get_name(queries[message.from_user.id][-1])[0][0],
                         queries[message.from_user.id][-1],
                         database.get_contact(queries[message.from_user.id][-1])[0][0])


@dp.message_handler(commands='rus_instr', state="*")
async def russian_instructure(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id,
                           text="Привет!\n\nУ всех нас есть люди, о которых мы проявляем заботу, но иногда это бывает слишком навязчиво...\n\nВ таких случаях я готов помочь Вам, выступив посредником в ваших отношениях\n\nС моей помощью Вы можете узнать, где тот или иной человек находится или как у него дела без прямого контакта.\n\nНажмите /start и наслаждайтесь возможностями:\n\n-/care, чтобы проверить локацию/состояние человека (через знак скрепки)\n\n-/feedback, чтобы оставить своём мнение о боте\n\nP.S. Используйте меня на смартфоне, а не на компьютере!"
                           )






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


