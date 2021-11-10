from main import bot, dp

def unpack_geo(geopositions: list):
    return '\n'.join(geopositions)

async def register(id: int):
    await bot.send_message(chat_id=id, text="You've already been registered!")
