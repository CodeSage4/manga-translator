from fastapi import APIRouter

router = APIRouter()

@router.get("/translation/health")
async def translation_health():
    return {"status": "translation endpoint is working"}