# Pdf2Quiz - FastAPI Cloud


## Prerequisites
- python3.8 +
- GCP Compute Engine (ubuntu)
- GCP Cloud Storage
- GCP Cloud SQL(mysql)
- GCP Cloud Memorystore
- [GCP credential](https://cloud.google.com/storage/docs/reference/libraries)
  
  
## Installation
```
sh install.sh
```

## Configuration
Update information in `CNF.py`
```

BUCKET_NAME = ""
BROKER_URL = "redis://0.0.0.0:6379/0"
DB_USER = ""
DB_PASSWORD = ""
DB_HOST = ""
DB_DATABASE = ""

```

## Running FastAPI
```
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=<absolute_path_of_your_credential.json>
uvicorn main:app --host 0.0.0.0 --port 8080
```

## Running Celery Worker
```
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=<absolute_path_of_your_credential.json>
celery -A celery_worker.celery worker --loglevel=info
```
