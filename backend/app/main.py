from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from models import *
from config import *

from routes import hello, user_request, user_authentication, user_signup, user_view_requests

origins = [
    "*"
]

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    SessionMiddleware,
    secret_key="adbms"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello.router)
app.include_router(user_request.router)
app.include_router(user_signup.router)
app.include_router(user_authentication.router)
app.include_router(user_view_requests.router)