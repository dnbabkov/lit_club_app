from sqlalchemy import Column, Integer, String, Enum
from lit_club_app.backend.db.base import Base

from lit_club_app.backend.common.enums import UploadedFileTypes


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    file_kind = Column(Enum(UploadedFileTypes), nullable=False)
