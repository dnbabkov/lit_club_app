import os
import pathlib
import random

from dotenv import load_dotenv

load_dotenv()

project_path = pathlib.Path(os.path.abspath(__file__)).parent.parent.parent
file_name = project_path / pathlib.Path(str(os.environ.get("MIME_FILE")))
max_file_size = int(os.environ.get("MAX_MIME_SIZE", "100000"))


def add_phrase(phrase):
    phrase = phrase + "\n"

    f = open(file_name, "r+")

    if os.path.getsize(file_name) > max_file_size:
        return "Попроси Саню расширить хранилище слов или удалить ненужные фразочки, я переполнен"

    lines = f.readlines()
    for i in range(len(lines)):
        if phrase.lower() == lines[i].lower():
            return "Я уже знаю эту фразочку :)"

    f.write(phrase)
    f.close()
    return "Запомнил!"


def cite():
    f = open(file_name, "r")
    lines = f.readlines()
    f.close()

    n = len(lines)
    if n == 0:
        return

    line_num = random.randint(0, n - 1)
    return lines[line_num]
