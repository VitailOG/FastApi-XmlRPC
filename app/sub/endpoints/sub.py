from fastapi import APIRouter, exceptions

router = APIRouter()


@router.get('/')
async def t():
    raise exceptions.HTTPException(status_code=402)
    return {}
