import re
from typing import NamedTuple, List

from io import BytesIO
from PIL import Image
from telethon.tl.types import MessageMediaPhoto
import pathlib

from features import mime, stalin, pants, logger
import os
import lit_club_app.backend.shark.service as shark
from lit_club_app.backend.users.service import user_service
from lit_club_app.backend.books.service import book_service
from lit_club_app.backend.reviews.service import review_service
from lit_club_app.backend.shark.service import achievement_service

user_help_str = """<b><u>Команды ботецкого:</u></b>
<b>!запомни <i>фраза</i></b> - бот запоминает вашу фразу и пополняет свой словарный запас.
<i>Пример</i>: !запомни я лучший бот
<b>!голос <i>"название книги" балл</i></b> - укрепить позиции демократии и проголосовать за книгу.
<i>Пример</i>: !голос "красный смех" 5
<b>!топ</b> - топ прочитанных книг.
<b>!ачивка <i>@пользователь "название ачивки" "описание ачивки"</i></b> - выдать члену клуба заслуженную ачивку, обязательно приложить картинку, желательно квадратную, чтобы бот ее не обрезал.
<i>Пример</i>: !ачивка @Ahdjdjx "сильная женщина" "да, я атеистка. и мне не стыдно заявить об этом по американскому телевидению"
<b>!ачивки <i>[@пользователь]</i></b> - показывает ачивки пользователя. Если не указать пользователя, покажет ваши ачивки.
<b>!ачивки_подробно <i>[@пользователь]</i></b> - показывает ачивки с их айдишником, нужно для того, чтобы удалить ачивки.
<b>!удали_ачивку <i>id_ачивки</i></b> - удаляет ачивку. Можно удалять только ачивки, которые вы сами выдали. После удаления ачивки айди других ачивок может измениться.
<i>Пример</i>: !удали_ачивку 10
<b>!орда</b> - тегает всех членов клуба
"""
admin_help_str = """<b><u>Команды админов:</u></b>
<b>!добавь_книгу <i>"название книги" балл год1-год2</i></b> - добавляет в топ книг новую книгу.
<i>Пример</i>: !добавь_книгу "маленький принц" 5 2025-2026
<b>!добавь_члена <i>@тг_айди роль</i></b> - добавляет в клуб нового члена.
<i>Пример</i>: !добавь_члена @Ahdjdjx user
<b>!дай_роль <i>@тг_айди роль</i></b> - дает члену новую роль.
<i>Пример</i>: !дай_роль @Ahdjdjx admin
<b>!удали_члена <i>@тг_айди</i></b> - удаляет члена.
<i>Пример</i>: !удали_члена @Ahdjdjx
<b>!обнови_айди <i>айди @новый_тг_айди</i></b> - обновляет тг айди члена, нужно, если человек его изменил.
Пример: !обнови_айди 111 @Ahdjdjx
<i>Пример</i>: !удали_члена @Ahdjdjx
<b>!члены</b> - показывает всех зарегистрированных в боте пользователей.
"""

bot_path = pathlib.Path(os.path.abspath(__file__)).parent.parent
achievements_path = bot_path / 'achievements/'

class service_ans(NamedTuple):
    msg: str = ""
    files_paths : List[str] | None = None
    files_captions: List[str] | None = None

def normalize_quotes(text: str) -> str:
    quote_regex = re.compile(r'[«»„“”]')
    return quote_regex.sub('"', text)

def get_user_id_from_event(event):
    return event.from_id.user_id if event.is_group else event.peer_id.user_id

async def get_user_id_from_tg_id(client, event):
    try:
        if event.message.message[event.message.entities[0].offset:event.message.entities[0].offset+event.message.entities[0].length] == '@BarkilfedroBot':
            ent = await client.get_entity(
                event.message.message[event.message.entities[1].offset:event.message.entities[1].offset+event.message.entities[1].length]
            )
        else:
            ent = await client.get_entity(
                event.message.message[event.message.entities[0].offset:event.message.entities[0].offset+event.message.entities[0].length]
            )
        user_id = ent.id
        return user_id
    except Exception as e:
        return f"exception when extracting tg_id: {e}"


async def handle_service_msg(msg, event, client, db) -> service_ans:
    service_msg, _, content = msg.partition(' ')
    content = normalize_quotes(content) if content else None

    user_id = get_user_id_from_event(event)
    user_role = user_service.get_user_role(db, user_id)
    # logger.log(user_role)

    if user_role == None:
        return service_ans('Ты не имеешь права о ты не имеешь права')
    user_role = user_role

    if service_msg == '!запомни' and content != None:
        return service_ans(mime.add_phrase(content))

    elif service_msg == '!голос':
        return service_ans(vote(db, content, event))

    # elif service_msg == '!добавь_книгу':
    #     if user_role != 'admin':
    #         return service_ans('Ты не имеешь права о ты не имеешь права')
    #     return service_ans(add_book(content, user_id))

    elif service_msg == '!топ':
        return service_ans(get_rating(db))

    elif service_msg == '!ачивка':
        return service_ans(await give_achievement(db, content, event, client, user_id))

    elif service_msg == '!ачивки':
        msg, achievements = await get_achievements(content, event, client, db)
        if achievements == None:
            return service_ans(msg)
        achievement_paths, achievement_ids = map(list, zip(*achievements))
        return service_ans(msg, achievement_paths)

    elif service_msg == '!ачивки_подробно':
        msg, achievements = await get_achievements(content, event, client, db)
        if achievements == None:
            return service_ans(msg)
        achievement_paths, achievement_ids = map(list, zip(*achievements))
        return service_ans(msg, achievement_paths, achievement_ids)

    elif service_msg == '!удали_ачивку':
        return service_ans(delete_achievement(content, user_id, user_role, db))

    elif service_msg == '!добавь_члена':
        if user_role != 'admin':
            return service_ans('Ты не имеешь права о ты не имеешь права')
        return service_ans(await add_user(content, client, event))

    elif service_msg == '!дай_роль':
        if user_role != 'admin':
            return service_ans('Ты не имеешь права о ты не имеешь права')
        return service_ans(update_role(content))

    elif service_msg == '!удали_члена':
        return service_ans(user_service.delete_user(content))

    elif service_msg == '!члены':
        if user_role != 'admin':
            return service_ans('Ты не имеешь права о ты не имеешь права')
        return service_ans(user_service.get_user_service())

    elif service_msg == '!обнови_айди':
        return service_ans(update_tg_id(content))

    elif service_msg == '!орда':
        ids_list = user_service.get_all_tg_ids(db)
        ids = ''
        for user_id in ids_list:
            if user_id != 'niger':
                ids += user_id + ' '

        return service_ans(ids)

    elif service_msg == '!помощь':
        msg = user_help_str
        if user_role == 'admin':
            msg += '\n' + admin_help_str
        return service_ans(msg)

    else:
        return service_ans('Я не знаю такой команды :( используй !помощь, чтобы получить список команд')

def vote(db, content, event):
    user_tg_id = get_user_id_from_event(event)

    split_content = content.split('"')
    if len(split_content) != 3 or split_content[2] == '':
        return 'Неправильно написана команда.\nПример: !голос "затерянный мир" 5'

    book_name = split_content[1].lower()

    try:
        score = int(split_content[2].strip())
    except ValueError:
        return 'Неправильно написана команда.\nПример:!голос "затерянный мир" 5'

    book = book_service.get_book_by_name(db, book_name)
    user_id = user_service.get_user_id_by_tg_id(db, user_tg_id)
    review_service.create_or_update_review(db, user_id, book.id, score, False, None)

    return 'Ваш голос учтен :)'

def add_book(content, user_id):
    match = re.match(r'\"(?P<book_name>[\w ]*)\" (?P<score>\d) (?P<epoch>\d\d\d\d-\d\d\d\d)', content)
    if match == None:
        return 'Неправильно написана команда.\nПример: !добавь_книгу "от полудня до полуночи" 5 2025-2026'
    book_name = match.group('book_name')
    score = int(match.group('score'))
    epoch = match.group('epoch')
    return stalin.add_book(user_id, book_name, score, epoch)

def get_rating(db):
    rating = review_service.get_rating(db)

    rating_dict = {}
    for r in rating:
        rating_dict[r[0]] = r[0] + ' ' + str(round(r[1], 2))
    msg = ''
    for key, val in rating_dict.items():
        msg += f"<b><u>{val}</u></b>\n"
    return msg

async def give_achievement(db, content, event, client, giver_id):
    if event.media == None or type(event.media) != MessageMediaPhoto:
        return 'Вы забыли приложить фотографию к ачивке'
    split_content = content.split('"')
    if len(split_content) != 5:
        return 'Неправильный формат команды. Правильный: !ачивка @пользователь "название" "описание"'

    data = await event.download_media(bytes)

    user_id = await get_user_id_from_tg_id(client, event)
    if user_id == None:
        return 'Вы забыли упомянуть пользователя.\nПример команды: !ачивка @пользователь "название" "описание"'

    achievement_image = Image.open(BytesIO(data))
    achievement_title = split_content[1]
    achievement_description = split_content[3]

    return achievement_service.give_achievement(
        db,
        user_id, 
        giver_id, 
        achievement_title, 
        achievement_description, 
        achievement_image
    )

async def get_achievements(content, event, client, db):
    if content == None:
        user_id = get_user_id_from_event(event)
    else:
        user_id = await get_user_id_from_tg_id(client, event)
        if user_id == None:
            return 'Вы ввели несуществующего пользователя', None

    achievements = list(achievement_service.get_user_achievement_paths(db, user_id))
    achievement_paths = [(achievements_path / str(achievement[0]), achievement[1]) for achievement in achievements]
    if achievement_paths == None or len(achievement_paths) == 0:
        return 'У этого пользователя нет ачивок', None

    return 'Вот такие вот ачивки', achievement_paths

def delete_achievement(content, user_id, role, db):
    try:
        achievement_id = int(content)
    except:
        return 'Вы передали неправильный идентификатор ачивки', None

    achievement_giver_id = achievement_service.get_achievement_giver_id(db, achievement_id)
    if achievement_giver_id == None:
        return 'Почему-то не получилось достать айди давателя ачивки, ткни санька', None
    achievement_giver_id = int(achievement_giver_id)

    if role == 'admin' or achievement_giver_id == user_id:
        achievement_service.delete_achievement(db, achievement_id)

    return 'Ачивка успешно удалена!'

async def add_user(content, client, event):
    content = content.split(' ')
    if len(content) != 2:
        return 'Неправильный формат команды. Правильный: !добавь_члена @айди роль'
    
    user_id = await get_user_id_from_tg_id(client, event)
    if user_id == None:
        return 'Не нашел user_id. Правильный формат команды: !добавь_члена @айди роль'
    
    return user_service.add_user(user_id, content[0], content[1])

def update_role(content):
    content = content.split(' ')
    if len(content) != 2:
        return 'Неправильный формат команды'
    
    return user_service.update_role(content[0], content[1])

def update_tg_id(content):
    content = content.split(' ')
    if len(content) != 2:
        return 'Неправильный формат команды'
    
    return user_service.update_tg_id(content[0], content[1])
