import json

from celery import Celery

import CNF
import crud
import schemas
import utils
from database import SessionLocal

celery = Celery("tasks", broker=CNF.BROKER_URL)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@celery.task
def make_quizzes(pdf_name, pdf_id):
    print("hello")
    db = next(get_db())
    meaningful_text = utils.extract_text(pdf_name)
    keyword = utils.extract_keyword(meaningful_text)
    results = utils.generate_quiz(pdf_name, keyword)
    for result in results:
        quiz = schemas.QuizCreate
        quiz.answer = result["answer"]
        quiz.options = json.dumps(result["options"])
        quiz.original_image = result["original_image"]
        quiz.masked_image = result["masked_image"]
        quiz.pdf_id = pdf_id

        result = crud.create_quiz(db=db, quiz=quiz)

    pdf = schemas.Pdf
    pdf.id = pdf_id
    result = crud.activate_pdf(db=db, pdf=pdf)
