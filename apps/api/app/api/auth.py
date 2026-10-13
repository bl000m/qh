from fastapi import APIRouter, Depends

from app.api.security import authenticated_subject
from app.core.models import SubjectId

router = APIRouter()


@router.get("/auth/me")
async def me(subject: SubjectId = Depends(authenticated_subject)) -> dict[str, str]:
    return {"user_id": subject}
