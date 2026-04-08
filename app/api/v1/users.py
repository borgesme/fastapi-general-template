from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserUpdate, UserResponse, UserPasswordUpdate
from app.schemas.base import ApiResponse
from app.services.user_service import UserService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(user: User = Depends(get_current_user)):
    return ApiResponse(msg="success", data=user)


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    updated = await service.update(user, data)
    return ApiResponse(msg="更新成功", data=updated)


@router.put("/me/password", response_model=ApiResponse[None])
async def change_password(
    data: UserPasswordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.update_password(user, data.old_password, data.new_password)
    return ApiResponse(msg="密码修改成功", data=None)
