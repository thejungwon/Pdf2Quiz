import json
import uuid
from typing import List, Union

import aiofiles
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud
import models
import schemas
import utils
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/pdfs/", response_model=List[schemas.PdfList])
def read_pdfs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pdfs = crud.get_pdfs(db, skip=skip, limit=limit)
    for pdf in pdfs:
        if len(pdf.quizzes):
            pdf.thumbnail = pdf.quizzes[0].original_image
        else:
            pdf.thumbnail = ""
    return pdfs


@app.get("/pdfs/{pdf_id}", response_model=schemas.Pdf)
def read_pdf(pdf_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_pdf(db, pdf_id=pdf_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/pdfs/", response_model=List[schemas.Pdf])
async def create_pdf(
    files: List[UploadFile],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    res = []
    for file in files:
        file_name = file.filename
        ext = file_name.split(".")[-1]
        file_path = "pdfs/" + uuid.uuid4().hex + "." + ext

        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()  # async read
            await out_file.write(content)  # async write
            pdf = schemas.PdfCreate
            pdf.file_name = file_name
            pdf.file_path = file_path
            result = crud.create_pdf(db=db, pdf=pdf)

            background_tasks.add_task(make_quizzes, file_path, result.id)
            res.append(result)
    return res


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
