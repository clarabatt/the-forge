from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_resumes():
    # TODO: implement after auth middleware
    return []
