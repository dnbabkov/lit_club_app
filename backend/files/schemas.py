from pydantic import BaseModel, ConfigDict

from lit_club_app.backend.common.enums import UploadedFileTypes

class UploadedFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str
    size_bytes: int
    file_kind: UploadedFileTypes

class BookCoverRead(BaseModel):
    id: int
    original_filename: str
    content_type: str
    size_bytes: int
    url: str

class BookFileRead(BaseModel):
    id: int
    original_filename: str
    content_type: str
    size_bytes: int
    download_url: str