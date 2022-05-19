import uuid
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.cloud import storage
from sqlalchemy.orm import Session

import CNF
import crud
import models
import schemas
from celery_worker import make_quizzes
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
    db: Session = Depends(get_db),
):
    res = []
    storage_client = storage.Client()
    bucket = storage_client.bucket(CNF.BUCKET_NAME)
    for file in files:
        file_name = file.filename
        ext = file_name.split(".")[-1]
        file_path = "pdfs/" + uuid.uuid4().hex + "." + ext

        content = await file.read()

        blob = bucket.blob(file_path)
        blob.upload_from_string(content, content_type="application/pdf")
        file_path = blob.public_url
        pdf = schemas.PdfCreate
        pdf.file_name = file_name
        pdf.file_path = file_path
        result = crud.create_pdf(db=db, pdf=pdf)

        make_quizzes.delay(file_path, result.id)
        res.append(result)
    return res
