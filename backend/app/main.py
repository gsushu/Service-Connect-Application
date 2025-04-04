from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from models import *
from config import *

from routes import hello, user_request, user_authentication, user_view_requests, user_view_services
from routes import worker_authentication, worker_accept_request, worker_view_all_open_requests, worker_view_my_requests, worker_complete_cancel_request


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
app.include_router(user_authentication.router)
app.include_router(user_view_requests.router)
app.include_router(user_view_services.router)
app.include_router(worker_authentication.router)
app.include_router(worker_view_all_open_requests.router)
app.include_router(worker_accept_request.router)
app.include_router(worker_view_my_requests.router)
app.include_router(worker_complete_cancel_request.router)