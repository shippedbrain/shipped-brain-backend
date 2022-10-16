from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.prediction_server import prediction

app = FastAPI(title='Shipped Brain - Prediction Server', version='0.1')

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
app.include_router(prediction.router, tags=['serving'], prefix='/api/v0')