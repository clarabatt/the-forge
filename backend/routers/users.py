from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_me():
    # TODO: implement after auth middleware
    return {"user": None}
