import random
import traceback
import re
import datetime
import pathlib
import os

from telethon import TelegramClient, events

from features import mime, web
from features import logger


from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from lit_club_app.backend.core.config import settings

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

engine = create_engine(database_url)

SessionLocal = sessionmaker(bind=engine,
                            expire_on_commit=False,
                            )
db = SessionLocal()

api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

bot_path = pathlib.Path(os.path.abspath(__file__)).parent
bot = TelegramClient(bot_path, api_id, api_hash).start(bot_token=bot_token)

@bot.on(events.NewMessage)
async def my_event_handler(event):
    msg = event.message.message
    msg = re.sub(r'^\@[\d\_\w]+ *', '', msg)
    
    time = str(event.message.date.astimezone())

    sender = await event.get_sender()
    username = sender.username
    if not username:
        username = sender.first_name
    
    logger.log(time + " " + username + " " + msg)

    if len(msg) == 0 or msg[0] != '!':
        if event.is_private or event.mentioned or random.randint(1, 100) <= 2:
            await event.reply(mime.cite())
            logger.log(time + ' ответил на упоминание')
        return

    if msg[0] == '!' and not (event.is_private or event.mentioned):
        return
    
    try:
        answer = await web.handle_service_msg(msg, event, bot, db)
    except Exception as e:
        logger.log(time + ' ' + traceback.format_exc())
        await event.reply('у меня под капотом что-то наебнулось')
        return
    
    logger.log(time + ' мой ответ')
    logger.log(answer.msg)
    
    await event.reply(answer.msg, parse_mode="html")
    
    if answer.files_paths != None and answer.files_captions != None:
        for path, caption in zip(answer.files_paths, answer.files_captions):
            await bot.send_file(event.chat_id, file=path, caption=str(caption), reply_to=event.message.reply_to_msg_id)
    
    if answer.files_paths != None and answer.files_captions == None:
        for path in answer.files_paths:
            await bot.send_file(event.chat_id, file=path, reply_to=event.message.reply_to_msg_id)

bot.start() 
bot.run_until_disconnected()
