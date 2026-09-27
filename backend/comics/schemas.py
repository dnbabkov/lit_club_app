from pydantic import BaseModel, Field, ConfigDict, model_validator


class PageWrite(BaseModel):
    id: int | None = Field(default=None, gt=0)
    number: int = Field(gt=0, le=2147483647)
    file_index: int | None = Field(default=None, ge=0)


class ChapterWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    number: int = Field(gt=0, le=2147483647)
    is_public: bool = False
    pages: list[PageWrite] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def unique_pages(self):
        numbers = [page.number for page in self.pages]
        ids = [page.id for page in self.pages if page.id is not None]
        if len(set(numbers)) != len(numbers) or len(set(ids)) != len(ids):
            raise ValueError("Номера страниц и идентификаторы не должны повторяться")
        return self


class PageRead(BaseModel):
    id: int
    number: int
    image_url: str


class ChapterSummary(BaseModel):
    id: int
    title: str
    number: int
    is_public: bool
    cover_url: str | None
    page_count: int


class ChapterRead(ChapterSummary):
    pages: list[PageRead]
