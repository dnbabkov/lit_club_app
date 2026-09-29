from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.backend.users.models import User
from lit_club_app.backend.shark.models import Achievement

class AchievementRepository:
    def create(self, db: Session, user_id: int, achievement_path: str, giver_id: int,
               title: str | None = None, description: str | None = None) -> Achievement:
        achievement = Achievement(user_id=user_id, path=str(achievement_path), giver_id=giver_id,
                                  title=title, description=description)
        try:
            db.add(achievement)
            db.flush()
            db.refresh(achievement)
            db.commit()
            return achievement
        except Exception:
            db.rollback()
            raise

    def get_achievement_paths_by_user_id(self, db: Session, user_id: int):
        expr = select(Achievement.path, Achievement.id).where(Achievement.user_id == user_id)
        res = db.execute(expr).all()
        return res

    def get_achievement_giver_id(self, db: Session, achievement_id: int):
        expr = select(Achievement.giver_id).where(Achievement.id == achievement_id)
        result = db.execute(expr)
        return result.scalar_one_or_none()

    def get(self, db: Session, achievement_id: int) -> Achievement | None:
        return db.get(Achievement, achievement_id)

    def delete_achievement(self, db: Session, achievement_id: int):
        achievement = db.get(Achievement, achievement_id)
        if achievement is None:
            return None
        db.delete(achievement)
        db.commit()
        return achievement
