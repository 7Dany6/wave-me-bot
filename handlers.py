from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

import asyncio
import logging
import sqlite3
import numpy

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
location_names = defaultdict(list)
coordinates = defaultdict(dict)


@dp.message_handler(commands="start", state="*")
async def intro_function(message):
    if database.user_exists(message.from_user.id):
        await register(message.from_user.id)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_agree = types.KeyboardButton(_("Agree"))
        button_disagree = types.KeyboardButton(_("Disagree"))
        keyboard.add(button_agree, button_disagree)
        await bot.send_message(message.from_user.id, text=_("Please, before using a bot, meet terms and conditions:\n{}").format(f'https://7daneksulimov.wixsite.com/hereiam'), reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == _("Disagree"), state="*")
async def terms_conditions_disagree(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_agree = types.KeyboardButton(_("Agree"))
    button_disagree = types.KeyboardButton(_("Disagree"))
    keyboard.add(button_agree, button_disagree)
    await bot.send_message(message.from_user.id, text=_("Sorry, firstly you need to agree with terms and conditions!"), reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == _("Agree"), state="*")
async def terms_conditions_agree(message: types.Message, state: FSMContext):
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

    @dp.message_handler(content_types=['contact', 'text'], state=Form.tracking)
    async def find_person(message: types.Message, state: FSMContext):
        if message.content_type == 'text' and (message.text[:-1] in (_("It's alright"), _('Let it snow'), _('Freezing'), _("I'm on fire")) or message.text[:-2] == _("Happy New Year")):
            print('here')
            await send_emoji(message=message)
        else:
            print('text name')
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
                await request_acceptance(message.from_user.id)
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
        print('here')
        polygon = Polygon([(message['location']['latitude'] + 0.002,
                            message['location']['longitude'] - 0.002),
                           (message['location']['latitude'] + 0.002,
                            message['location']['longitude'] + 0.002),
                           (message['location']['latitude'] - 0.002,
                            message['location']['longitude'] + 0.002),
                           (message['location']['latitude'] - 0.002,
                            message['location']['longitude'] - 0.002)])
        print(polygon)
        result = requests.get(
            url=f'https://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={message["location"]["longitude"]},{message["location"]["latitude"]}&format=json&lang=ru_RU')
        json_data = result.json()
        if database.existence_fav_locations(message.from_user.id):
            for value in database.coordinates(message.from_user.id):
                coordinates[message.from_user.id][(float(value[2]), float(value[1]))] = value[0]
            for coords, name in coordinates[message.from_user.id].items():
                print(coords)
                if polygon.contains(Point(coords[0], coords[1])):
                    await bot.send_message('{0}'.format(queries[message.from_user.id][-1]),
                                           text=_("User <a href='tg://user?id={1}'>{0}</a> with number {2} is here: <a href='http://www.google.com/maps/place/{4},{5}'>{3}</a>").format(message.from_user.first_name, message.from_user.id, database.get_contact(message.from_user.id)[0][0], name, message["location"]["latitude"], message["location"]["longitude"]))
                    queries[message.from_user.id].pop()
                    await check_queries(queries, message.from_user.id)
                    return
        #result = requests.get(url=f'https://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={message["location"]["longitude"]},{message["location"]["latitude"]}&format=json&lang=ru_RU')
        #json_data = result.json()
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
        #last_geopositions[message.from_user.id].append(f"{json_data['response']['GeoObjectCollection']['featureMember'][1]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']}")  # база с координатами, временем, contact и кто просил
        await check_queries(queries, message.from_user.id)


    @dp.message_handler(content_types=["text"], state="*")
    async def send_emoji(message: types.Message):
        if not database.existence_received_emoji(queries[message.from_user.id][-1], message.from_user.id):
            if message.text[:-1] == _("It's alright"):
                database.add_to_received_emoji_if_victory(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-1] == _('Let it snow'):
                database.add_to_received_emoji_if_snowflake(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-1] == _('Freezing'):
                database.add_to_received_emoji_if_cold(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-2] == _('Happy New Year'):
                database.add_to_received_emoji_if_snowman(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-1] == _("I'm on fire"):
                database.add_to_received_emoji_if_fire(queries[message.from_user.id][-1], message.from_user.id)
        else:
            if message.text[:-1] == _("It's alright"):
                database.increase_received_victory_emoji_counter(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-1] == _('Let it snow'):
                database.increase_received_snowflake_emoji_counter(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-1] == _('Freezing'):
                database.increase_received_cold_emoji_counter(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-2] == _('Happy New Year'):
                database.increase_received_snowman_emoji_counter(queries[message.from_user.id][-1], message.from_user.id)
            elif message.text[:-1] == _("I'm on fire"):
                database.increase_received_fire_emoji_counter(queries[message.from_user.id][-1], message.from_user.id)
        if not database.user_existance(queries[message.from_user.id][-1], message.from_user.id):
            database.add_to_tracking_trackable(queries[message.from_user.id][-1], database.get_contact(queries[message.from_user.id][-1])[0][0],
                                               message.from_user.id, database.get_contact(message.from_user.id)[0][0], database.get_name(message.from_user.id)[0][0])
        else:
            database.increase_counter(database.get_contact(queries[message.from_user.id][-1])[0][0], database.get_contact(message.from_user.id)[0][0])
        if message.text[:-1] == _("It's alright"):
            await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                                   text="\u270C")
        elif message.text[:-1] == _('Let it snow'):
            await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                                   text="\u2744")
        elif message.text[:-1] == _('Freezing'):
            await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                                   text="\U0001F976")
        elif message.text[:-2] == _('Happy New Year'):
            await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                                   text="\u2603")
        elif message.text[:-1] == _("I'm on fire"):
            await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                                   text="\U0001F525")
        await bot.send_message(chat_id='{0}'.format(queries[message.from_user.id][-1]),
                               text=_("From user <a href='tg://user?id={1}'>{0}</a> with number {2}!").format(
                                   database.get_name(message.from_user.id)[0][0], message.from_user.id,
                                   database.get_contact(message.from_user.id)[0][0])
                               , parse_mode=ParseMode.HTML)
        print('text below emoji')
        queries[message.from_user.id].pop()
        if len(queries[message.from_user.id]) != 0:
            await send_request(message.from_user.id,
                               database.get_name(queries[message.from_user.id][-1])[0][0],
                               queries[message.from_user.id][-1],
                               database.get_contact(queries[message.from_user.id][-1])[0][0])


@dp.message_handler(commands='instr', state="*")
async def instruction(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id,
                           text=_("Hi!\n\nWe all have people to care about and now you can do it not disturbing them sending a request with only one button!\n\nI'm glad to help you out\n\nWith my helping hand you can get where this ot that person is or you can get an emoji with his state.\n\nPress /start and enjoy:\n\n-/care to check location/state (through clip symbol)\n\n-/feedback to leave your opinion about bot\n\n-/sent to know how many emojis you've sent\n\n-/received to know how many emojis you've received\n\n-/add_place to add location to your favourite\n\nP.S. Use me via smartphone, not PC!"
                           ))

@dp.message_handler(commands='add_place', state="*")
async def add_location(message: types.Message):
    await bot.send_message(message.from_user.id, text=_("Please, enter the name of a location!"))
    await Form.enter_location.set()


@dp.message_handler(content_types=['text'], state=Form.enter_location)
async def name_location(message: types.Message):
    location_names[message.from_user.id].append(message.text.encode('utf-8'))
    print(location_names)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton(_("Share a location"), request_location=True)
    keyboard.add(button)
    await bot.send_message(message.from_user.id,
                           text=_("Please, <b>switch on your location</b> and press the button!"),
                           parse_mode=ParseMode.HTML,
                           reply_markup=keyboard)
    await Form.fav_location.set()


@dp.message_handler(content_types=['location'], state=Form.fav_location)
async def send_fav_location(message: types.Message, state: FSMContext):
    if not location_names[message.from_user.id]:
        await give_position(message=message)
    database.add_location_name(message.from_user.id, location_names[message.from_user.id].pop().decode('utf-8'),
                               message['location']['longitude'], message['location']['latitude'])
    await bot.send_message(message.from_user.id, text=_("Location has been registered!"))
    print(database.coordinates(message.from_user.id))
    await state.finish()



@dp.message_handler(commands="received", state="*")
async def return_number_received_emojis(message: types.Message):
    print('return received emojis')
    if not database.existence_received_emoji_user_received(message.from_user.id):
        await bot.send_message(message.from_user.id,
                               text=_("You haven't received emojis, send someone a request by clicking /care!"))
    else:
        await bot.send_message(message.from_user.id,
                               text=_("You've received: \n"
                                      "{0} {1}\n"
                                      "{2} {3}\n"
                                      "{4} {5}\n"
                                      "{6} {7}\n"
                                      "{8} {9}\n").format(database.count_received_emojis_victory(message.from_user.id)[0][0], "\u270C",
                                                          database.count_received_emojis_snowflake(message.from_user.id)[0][0], "\u2744",
                                                          database.count_received_emojis_cold(message.from_user.id)[0][0], "\U0001F976",
                                                          database.count_received_emojis_fire(message.from_user.id)[0][0], "\U0001F525",
                                                          database.count_received_emojis_snowman(message.from_user.id)[0][0], "\u2603"))



@dp.message_handler(commands="sent", state="*")
async def return_number_sent_emojis(message: types.Message):
    print('return sent emojis')
    if not database.existence_received_emoji_user_sent(message.from_user.id):
        await bot.send_message(message.from_user.id,
                               text=_("You haven't sent emojis yet!"))
    else:
        await bot.send_message(message.from_user.id,
                               text=_("You've sent: \n"
                                      "{0} {1}\n"
                                      "{2} {3}\n"
                                      "{4} {5}\n"
                                      "{6} {7}\n"
                                      "{8} {9}\n").format(database.count_sent_emojis_victory(message.from_user.id)[0][0], "\u270C",
                                                           database.count_sent_emojis_snowflake(message.from_user.id)[0][0], "\u2744",
                                                           database.count_sent_emojis_cold(message.from_user.id)[0][0], "\U0001F976",
                                                           database.count_sent_emojis_fire(message.from_user.id)[0][0], "\U0001F525",
                                                          database.count_sent_emojis_snowman(message.from_user.id)[0][0], "\u2603"))



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

