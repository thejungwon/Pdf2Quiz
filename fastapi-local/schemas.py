from datetime import datetime
from typing import List, Union

from pydantic import BaseModel

## 이게 맞나..


class QuizBase(BaseModel):
    answer: str
    options: str
    original_image: str
    masked_image: str
    pdf_id: int


class QuizCreate(QuizBase):
    pass


class Quiz(QuizBase):
    id: int

    class Config:
        orm_mode = True


class PdfBase(BaseModel):
    id: int
    file_name: str
    file_path: str
    is_ready: bool
    created_date: datetime

    class Config:
        orm_mode = True


class PdfList(PdfBase):
    thumbnail: str


class PdfCreate(PdfBase):
    pass


class Pdf(PdfBase):

    quizzes: List[Quiz] = []

    class Config:
        orm_mode = True
