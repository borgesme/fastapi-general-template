"""
订单 API（预留模块，Phase 2 实现）
"""
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/orders", tags=["订单管理"])
