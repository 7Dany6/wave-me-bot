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


@dp.message_handler(commands="start", state="*")
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
    if current_state is not None:
        await state.finish()
    logging.info('Cancelling state {}'.format(current_state))
    await cancel(message.from_user.id)


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

    @dp.message_handler(content_types=['contact', 'text'], state=Form.tracking)  # deleted state Form.tracking
    async def find_person(message: types.Message, state: FSMContext):
        if message.text == _("\u270C"):
            print('here')
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
        await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                               text=_("User <a href='tg://user?id={1}'>{0}</a> with number {2} is here:\n{3}").format(message.from_user.first_name, message.from_user.id, database.get_contact(message.from_user.id)[0][0], json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']),
                               parse_mode=ParseMode.HTML)  # changed parse mode
        await bot.send_location(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                                latitude=message['location']['latitude'],
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
    async def give_contact(message: types.Message):
        await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                               text=_("\u270C"))
        await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                               text=_("From user <a href='tg://user?id={1}'>{0}</a> with number {2}!").format(
                                   database.get_name(message.from_user.id)[0][0], message.from_user.id,
                                   database.get_contact(message.from_user.id)[0][0])
                               , parse_mode=ParseMode.HTML)
        if not database.existence_received_emoji(queries[message.from_user.id][-1]):
            database.add_to_received_emoji(queries[message.from_user.id][-1], message.from_user.id)
        else:
            database.increase_received_emoji_counter(queries[message.from_user.id][-1], message.from_user.id)
        queries[message.from_user.id].pop()
        if len(queries[message.from_user.id]) != 0:
            await send_request(message.from_user.id,
                               database.get_name(queries[message.from_user.id][-1])[0][0],
                               queries[message.from_user.id][-1],
                               database.get_contact(queries[message.from_user.id][-1])[0][0])


@dp.message_handler(commands='rus_instr', state="*")
async def russian_instruction(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id,
                           text="Привет!\n\nУ всех нас есть люди, о которых мы проявляем заботу, теперь есть возможность делать это, не отвлекая близких людей, послав им запрос всего одной кнопкой!\n\nЯ готов помочь Вам, выступив посредником в ваших отношениях\n\nС моей помощью Вы можете узнать, где тот или иной человек находится или получить от него эмоджи.\n\nНажмите /start и наслаждайтесь возможностями:\n\n-/care, чтобы проверить локацию/состояние человека (через знак скрепки)\n\n-/feedback, чтобы оставить своём мнение о боте\n\n-/sent, чтобы посмотреть, сколько эмоджи Вы отправили\n\n-/received, чтобы посмотреть, сколько эмоджи Вы получили\n\nP.S. Используйте меня на смартфоне, а не на компьютере!"
                           )


@dp.message_handler(commands="received", state="*")
async def return_number_received_emojis(message: types.Message):
    print('return received emojis')
    if not database.existence_received_emoji(message.from_user.id):
        await bot.send_message(message.from_user.id,
                               text=_("You haven't received {0}, send someone a request by clicking /care!").format('\u270C'))
    else:
        await bot.send_message(message.from_user.id,
                               text=_("{1} received:{0}!").format(database.count_received_emojis(message.from_user.id)[0][0], '\u270C'))


@dp.message_handler(commands="sent", state="*")
async def return_number_sent_emojis(message: types.Message):
    print('return sent emojis')
    if not database.existence_received_emoji(message.from_user.id):
        await bot.send_message(message.from_user.id,
                               text=_("You haven't sent {0} yet!").format('\u270C'))
    else:
        await bot.send_message(message.from_user.id,
                               text=_("{1} sent:{0}!").format(
                                   database.count_sent_emojis(message.from_user.id)[0][0], '\u270C'))


@dp.message_handler(commands="feedback", state='*')
async def feedback(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    print(current_state)
    if current_state:
        await state.finish()
    await bot.send_message(message.from_user.id, text=_("Leave your opinion, it will improve the bot!"))
    await Form.feedback.set()
    current_state = await state.get_state()
    print(current_state)

@dp.message_handler(content_types=['text'], state=Form.feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    print("comment")
    await bot.send_message(USER_ID,
                           text=f"Feedback from [{message.from_user.first_name}](tg://user?id={message.from_user.id}): {message.text}",
                           parse_mode=ParseMode.MARKDOWN_V2)
    await state.finish()

