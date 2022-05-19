from sqlalchemy.orm import Session

import models
import schemas


def get_pdfs(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Pdf)
        .order_by(models.Pdf.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_pdf(db: Session, pdf_id: int):
    return db.query(models.Pdf).filter(models.Pdf.id == pdf_id).first()


def create_pdf(db: Session, pdf: schemas.PdfCreate):

    db_pdf = models.Pdf(
        file_name=pdf.file_name,
        file_path=pdf.file_path,
    )
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    return db_pdf


def activate_pdf(db: Session, pdf: schemas.PdfBase):
    # get the existing data
    db_pdf = db.query(models.Pdf).filter(models.Pdf.id == pdf.id).one_or_none()
    if db_pdf is None:
        return None

    # Update model class variable from requested fields

    db_pdf.is_ready = True
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    return db_pdf


def create_quiz(db: Session, quiz: schemas.QuizCreate):

    db_quiz = models.Quiz(
        answer=quiz.answer,
        options=quiz.options,
        original_image=quiz.original_image,
        masked_image=quiz.masked_image,
        pdf_id=quiz.pdf_id,
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz
