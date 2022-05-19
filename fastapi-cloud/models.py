import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from database import Base


class Pdf(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(Text)
    file_path = Column(Text)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_ready = Column(Boolean, default=False)

    quizzes = relationship("Quiz", back_populates="owner")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    answer = Column(Text)
    options = Column(Text)
    original_image = Column(Text)
    masked_image = Column(Text)

    pdf_id = Column(Integer, ForeignKey("pdfs.id"))

    owner = relationship("Pdf", back_populates="quizzes")
