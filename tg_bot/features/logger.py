import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

project_path = pathlib.Path(os.path.abspath(__file__)).parent.parent
log_file = project_path / pathlib.Path(str(os.environ.get('LOG_FILE')))
old_log_file = project_path / pathlib.Path(str(os.environ.get('OLD_LOG_FILE')))
max_file_size = int(os.environ.get('MAX_LOG_SIZE', '10000'))

def log(msg):
    msg = msg + '\n'

    with open(log_file, 'a+') as log:
        log.seek(0)

        if os.path.getsize(log_file) > max_file_size:
            with open(old_log_file, 'w') as old_log:
                old_log.write(log.read())

            log.seek(0)
            log.truncate()

        log.write(msg)
