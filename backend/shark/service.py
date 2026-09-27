from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from lit_club_app.backend.shark.repository import AchievementRepository
from lit_club_app.backend.users.repository import UserRepository

import sqlite3
import pathlib
import os

from PIL import Image, ImageDraw, ImageFont
import textwrap

db_address = "/home/soberjan/PythonProjects/lit_club_app/tg_bot/database.db"


bot_path = pathlib.Path(os.path.abspath(__file__)).parent.parent.parent / 'tg_bot/'
achievements_path = bot_path / 'achievements/'
ui_path  = bot_path / 'UIElements'
background_img_path = ui_path / 'main_background.png'
frame_path = ui_path / 'frame.png'
frame  = ui_path / 'frame.png'
font_path = ui_path / 'americanhorrorstory.otf'
paper_texture_path = ui_path / 'paper_texture.png'
stump_path = ui_path / 'stump.png'


class AchievementService:
    def __init__(self):
        self.achievement_repo = AchievementRepository()
        self.user_repo = UserRepository()

    def create_achievement(self, picture, title_text, description_text):
        background = Image.open(background_img_path)

        picture = picture.resize((700, 700))
        picture_pos = (200, 200)
        background.paste(picture, picture_pos)

        frame = Image.open(frame_path)
        background = Image.alpha_composite(background, frame)


        title_font = ImageFont.truetype(font_path, 90)
        description_font = ImageFont.truetype(font_path, 50)
        text_color = (212, 207, 197)

        draw = ImageDraw.Draw(background)

        wrapped_title = textwrap.wrap(title_text, 20)
        title_pos = (980, 156)
        draw.text(title_pos, wrapped_title[0], font=title_font, fill=text_color)
        if len(wrapped_title) > 1:
            title_pos = (990, 280)
            draw.text(title_pos, wrapped_title[1], font=title_font, fill=text_color)

        wrapped_description = textwrap.wrap(description_text, 34)

        y = 410
        for text in wrapped_description:
            description_pos = (1020, y)
            draw.text(description_pos, text, font=description_font, fill=text_color)
            y += 60

        texture_background = Image.open(paper_texture_path)
        texture_background.putalpha(25)
        background = Image.alpha_composite(background, texture_background)

        stump = Image.open(stump_path)
        background = Image.alpha_composite(background, stump)

        achievement_id = len(os.listdir(achievements_path))
        background.save(achievements_path / f'{achievement_id}.png')
        return achievement_id

    def give_achievement(self, db, user_tg_id, giver_tg_id, title_str, description_str, picture):
        user_id = self.user_repo.get_by_tg_id(db, user_tg_id).id
        giver_id = self.user_repo.get_by_tg_id(db, giver_tg_id).id

        last_achievement_id = self.create_achievement(picture, title_str, description_str)
        achievement_path = achievements_path / f'{last_achievement_id}.png'

        self.achievement_repo.create(db, user_id, achievement_path, giver_id)

        return 'Ачивка успешно выдана :)'

    def get_user_achievement_paths(self, db, user_tg_id):
        user = self.user_repo.get_by_tg_id(db, user_tg_id)
        return self.achievement_repo.get_achievement_paths_by_user_id(db, user.id)

    def get_achievement_giver_id(self, db, achievement_id):
        giver_id = self.achievement_repo.get_achievement_giver_id(db, achievement_id)
        return giver_id

    def delete_achievement(self, db, achievement_id):
        giver_id = self.achievement_repo.delete_achievement(db, achievement_id)
        return giver_id


if __name__ == '__main__':
    pass


achievement_service = AchievementService()
