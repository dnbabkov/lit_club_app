from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from lit_club_app.backend.core.config import settings
from lit_club_app.backend.core.exceptions import ForbiddenFileTypeError, FileTooHeavyError

@dataclass
class SavedFileData:
    original_filename: str
    stored_filename: str
    storage_path: str
    content_type: str
    size_bytes: int

class FileService:
    chunk_size = 1024 * 1024

    def _get_extension(self, filename: str) -> str:
        return Path(filename).suffix.lower()

    async def save_uploaded_file(self,
                                 *,
                                 file: UploadFile,
                                 relative_dir: str,
                                 allowed_content_types: set[str],
                                 allowed_extensions: set[str],
                                 max_size_bytes: int
                                 ) -> SavedFileData:
        if file.content_type not in allowed_content_types:
            raise ForbiddenFileTypeError()

        original_filename = file.filename or "uploaded_file"
        extension = self._get_extension(original_filename)

        if extension not in allowed_extensions:
            raise ForbiddenFileTypeError()

        stored_filename = f"{uuid4().hex}{extension}"

        upload_dir = settings.upload_dir / relative_dir
        upload_dir.mkdir(parents=True, exist_ok=True)

        storage_path = upload_dir / stored_filename
        size_bytes = 0

        try:
            with storage_path.open("wb") as buffer:
                while chunk := await file.read(self.chunk_size):
                    size_bytes += len(chunk)

                    if size_bytes > max_size_bytes:
                        raise FileTooHeavyError()
                    buffer.write(chunk)
        except Exception:
            storage_path.unlink(missing_ok=True)
            raise

        return SavedFileData(
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=str(storage_path),
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes
        )

    def delete_file_safely(self, storage_path: str) -> None:
        Path(storage_path).unlink(missing_ok=True)

file_service = FileService()