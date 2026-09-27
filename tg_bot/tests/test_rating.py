from sqlalchemy import select
from features.web import handle_service_msg
from lit_club_app.backend.users.models import User
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.books.models import Book
from lit_club_app.backend.common.enums import Roles

from sqlalchemy.sql import insert, select

async def test_rating(mocker, db):
    empty = mocker.Mock()
    mocker.patch(
        'features.web.get_user_id_from_event',
         mocker.Mock(return_value=1)
    )

    user = User(username='niger', telegram_login='niger', tg_id='12345', password_hash='niger', role=Roles.MEMBER)
    db.add(user)
    book = Book(title='Майнкампф', normalized_title='Майнкапф', author='Фюрер', normalized_author='Фюрер')
    db.add(book)
    db.flush()

    await handle_service_msg('!голос "Майнкампф" 5', empty, empty, db)
    voting_message = await handle_service_msg('!топ', empty, empty, db)
    print(voting_message.msg)
    assert voting_message.msg == '<b><u>Майнкампф 5.00</u></b>\n'

