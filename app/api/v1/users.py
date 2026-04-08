from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserUpdate, UserResponse, UserPasswordUpdate
from app.services.user_service import UserService
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.helpers import MsgResponse

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    updated = await service.update(user, data)
    return updated


@router.put("/me/password", response_model=MsgResponse)
async def change_password(
    data: UserPasswordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.update_password(user, data.old_password, data.new_password)
    return MsgResponse(msg="密码修改成功")
