from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_health() -> dict[str, str]:
    return {"status": "ok", "service": "ASET API"}
