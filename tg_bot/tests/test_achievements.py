from features.web import handle_service_msg
from lit_club_app.backend.users.models import User
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.books.models import Book
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.shark.service import achievement_service

from sqlalchemy.sql import insert, select
from telethon.tl.types import MessageMediaPhoto

from io import BytesIO
from PIL import Image
import pathlib
import os
import shutil

def make_black_image_bytes():
    buffer = BytesIO()

    image = Image.new(
        "RGB",
        (100, 100),
        color="black"
    )

    image.save(buffer, format="PNG")

    return buffer.getvalue()

async def test_achievements(mocker, db):
    empty = mocker.Mock()
    mocker.patch(
        'features.web.get_user_id_from_event',
         mocker.Mock(return_value=1)
    )
    mocker.patch(
        'features.web.get_user_id_from_tg_id',
         mocker.AsyncMock(return_value=1)
    )

    mocker.patch(
        "lit_club_app.backend.shark.service.achievements_path",
        pathlib.Path(os.path.abspath(__file__)).parent / 'test_achievements'
    )

    event = mocker.Mock()
    event.media = MessageMediaPhoto(photo=None)
    event.download_media = mocker.AsyncMock(
        return_value=make_black_image_bytes()
    )

    mocker.patch(
        'features.web.get_user_id_from_event',
         mocker.Mock(return_value=1)
    )

    user = User(username='niger', telegram_login='@niger', tg_id=1, password_hash='niger', role=Roles.MEMBER)
    db.add(user)
    book = Book(title='Майнкампф', normalized_title='Майнкапф', author='Фюрер', normalized_author='Фюрер')
    db.add(book)
    db.flush()

    achievement_message = await handle_service_msg('!ачивка @niger "крутой перец" "черный как смола!"', event, empty, db)
    assert achievement_message.msg == 'Ачивка успешно выдана :)'

    achievement_message = await handle_service_msg('!ачивки @niger', event, empty, db)
    assert achievement_message.msg == 'Вот такие вот ачивки'
    assert achievement_message.files_paths == [str(pathlib.Path(os.path.abspath(__file__)).parent / 'test_achievements/0.png')]
    achievement_message = await handle_service_msg('!ачивки_подробно @niger', event, empty, db)
    assert achievement_message.msg == 'Вот такие вот ачивки'
    assert achievement_message.files_paths == [str(pathlib.Path(os.path.abspath(__file__)).parent / 'test_achievements/0.png')]
    assert achievement_message.files_captions == [1]
    achievement_message = await handle_service_msg('!удали_ачивку 1', event, empty, db)
    assert achievement_message.msg == 'Ачивка успешно удалена!'

    folder = pathlib.Path(os.path.abspath(__file__)).parent / 'test_achievements'
    for item in folder.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

