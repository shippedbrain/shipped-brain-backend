from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, ml_models, auth, hashtags, model_requests, model_uploads, model_likes, papers_with_code, model_comments, health_checks

app = FastAPI(
    title='Shipped Brain API',
    version='0.1'
)

# CORS setup
origins = [
    'http://localhost:4200',
    "http://shippedbrain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['*']
)

# Included routers
app.include_router(auth.router, tags=['auth'], prefix='/api/v0')
app.include_router(users.router, tags=['users'], prefix='/api/v0')
app.include_router(ml_models.router, tags=['ml_models'], prefix='/api/v0')
app.include_router(hashtags.router, tags=['hashtags'], prefix='/api/v0')
app.include_router(model_requests.router, tags=['model-requests'], prefix='/api/v0')
app.include_router(model_uploads.router, tags=['model-uploads'], prefix='/api/v0')
app.include_router(model_likes.router, tags=['model-likes'], prefix='/api/v0')
app.include_router(model_comments.router, tags=['model-comments'], prefix='/api/v0')
#app.include_router(papers_with_code.router, tags=['papers-with-code'], prefix='/api/v0')
app.include_router(health_checks.router, tags=['health-checks'], prefix='/api/v0/health')
