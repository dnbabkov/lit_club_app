from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.backend.common.enums import UploadedFileTypes
from lit_club_app.backend.files.models import UploadedFile


class FileRepository:
    def get_by_id(self, db: Session, file_id: int) -> UploadedFile | None:
        statement = select(UploadedFile).where(UploadedFile.id == file_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def create_file_record(self,
                           db: Session,
                           *,
                           original_filename: str,
                           stored_filename: str,
                           storage_path: str,
                           content_type: str,
                           size_bytes: int,
                           file_kind: UploadedFileTypes
                           ) -> UploadedFile:
        uploaded_file = UploadedFile(
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            file_kind=file_kind
        )
        db.add(uploaded_file)
        db.flush()

        return uploaded_file

    def delete_file_record(self, db: Session, uploaded_file: UploadedFile):
        db.delete(uploaded_file)
        db.flush()