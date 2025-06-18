from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

@router.get("")
async def hello_world():
    """Simple hello world api"""
    return {"message": "Hello World"}

