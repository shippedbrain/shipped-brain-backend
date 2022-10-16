from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.upload_server import ml_models_upload

app = FastAPI()

# CORS setup
origins = [
    'http://localhost:8000',
    'http://localhost:4200',
    "http://shippedbrain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ['POST'],
    allow_headers = ['*']
)

# Included routers
app.include_router(ml_models_upload.router, tags = ['ml_models_upload'])