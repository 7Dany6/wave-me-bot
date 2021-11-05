buttons = ["Feedback", "Cancel", "Delete an account", "Track a person"]
buttons_for_tracked_person = ['Yes', 'No']
buttons_for_last_geopositions = ['Yep', 'Nope']
buttons_for_track_a_person = ["Track a geoposition", "Look at last geopositions", "Cancel"]
button_ignore = types.KeyboardButton("I'm OK")
            keyboard.add(button_location, button_reject, button_ignore)
if len(queries[message.from_user.id]) == 0:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    await bot.send_message(message.from_user.id,
                           text=f'Please, choose your further action!',
                           reply_markup=keyboard)

