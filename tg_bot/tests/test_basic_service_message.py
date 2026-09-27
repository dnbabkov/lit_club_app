from sqlalchemy import select
from features.web import handle_service_msg
from lit_club_app.backend.users.models import User
from lit_club_app.backend.common.enums import Roles

from sqlalchemy.sql import insert

async def test_basic_service_msg(mocker, db):
    empty = mocker.Mock()

    mocker.patch(
        'features.web.get_user_id_from_event',
         mocker.Mock(return_value=1)
    )

    user = User(username='niger', telegram_login='niger', tg_id='12345', password_hash='niger', role=Roles.MEMBER)
    db.add(user)
    db.flush()

    query = select(User.role).where(User.id==user.id)
    res = db.execute(query).scalar()

    wrong_message = await handle_service_msg('!hi, niger', empty, empty, empty)

    assert wrong_message.msg == 'Я не знаю такой команды :( используй !помощь, чтобы получить список команд'
