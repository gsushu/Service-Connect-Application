from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/hello")
def hello(request: Request):
    user = request.session.get("user")
    if not user:
        return {"message": "Hello, guest!"}
    return {"message": f"Hello, {user['username']}! (user id: {user['id']})"}