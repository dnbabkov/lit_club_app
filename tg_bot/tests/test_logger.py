import features.logger as logger

async def test_log():
    logger.log_file = logger.project_path / 'tests/log.txt'
    logger.log_file.touch()
    logger.log('niger')
    file = open(logger.log_file)
    lines = file.readlines()
    assert lines[0] == 'niger\n'
    logger.log_file.unlink()
