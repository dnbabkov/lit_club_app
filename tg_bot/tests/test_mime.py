import features.mime as mime
from features.web import handle_service_msg

def test_mime():
    mime.file_name = mime.project_path / 'tests/mime.txt'
    mime.file_name.touch()
    mime.add_phrase('niger')
    assert mime.cite() == 'niger\n'
    mime.file_name.unlink()


async def test_mime_service_msg(mocker):
    event = mocker.Mock()
    event.get_role = mocker.Mock(return_value='niger')
    mocker.patch(
        "features.web.pants",
        event
    )

    mime.file_name = mime.project_path / 'tests/mime.txt'
    mime.file_name.touch()

    remembered_message = await handle_service_msg('!запомни нигер', event, event, event)
    assert remembered_message.msg == 'Запомнил!'

    mime.file_name.unlink()
