"""
식단 관련 라우터
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.diets.schema.schemas import MonthlyDietRequest, DietResponse, DietInfo
from app.base.base_response import BaseResponse
from app.core.database import get_db
from app.diets.services.diet_service import DietService
from app.core.constants import StatusCodes

logger = logging.getLogger(__name__)

router = APIRouter()

# DietService 인스턴스 생성
diet_service = DietService()


@router.post(
    "/diet/{user_id}",
    response_model=BaseResponse[DietResponse],
    status_code=status.HTTP_201_CREATED,
    summary="월별 식단 정보 저장",
    description="특정 사용자의 월별 식단 정보를 저장합니다. 해당 연월의 기존 데이터는 모두 삭제되고 새 데이터로 교체됩니다.",
    tags=["식단"]
)
async def save_diet(user_id: int, diet_data: MonthlyDietRequest, db: AsyncSession = Depends(get_db)):
    """
    월별 식단 정보 저장
    
    - **user_id**: 사용자 ID
    - **daily_diets**: 일별 식단 정보 목록
      - **day**: 일 (1-31)
      - **meals**: 해당 일의 식사 정보 목록
        - **meal_type**: 식사 타입 (breakfast, lunch, dinner, snack)
        - **food_name**: 음식 이름
        - **calories**: 칼로리
    - **year**: 년도
    - **month**: 월
    
    해당 사용자의 해당 연월에 기존에 저장된 모든 식단 데이터가 삭제되고, 새로 전송된 데이터로 교체됩니다.
    """
    try:
        result = await diet_service.save_diet(user_id, diet_data, db)
        return BaseResponse.of_success(StatusCodes.CREATED, result)
    except Exception as e:
        raise


@router.get(
    "/diet/{user_id}",
    response_model=BaseResponse[List[DietInfo]],
    status_code=status.HTTP_200_OK,
    summary="사용자 식단 정보 조회",
    description="특정 사용자의 식단 정보를 조회합니다. 년도와 월로 필터링 가능합니다.",
    tags=["식단"]
)
async def get_user_diets(
    user_id: int, 
    year: Optional[int] = Query(None, description="년도"),
    month: Optional[int] = Query(None, description="월"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 식단 정보 조회
    
    - **user_id**: 사용자 ID
    - **year**: 년도 (선택사항)
    - **month**: 월 (선택사항)
    
    년도와 월을 지정하지 않으면 모든 식단 정보를 반환합니다.
    """
    try:
        result = await diet_service.get_user_diets(user_id, year, month, db)
        return BaseResponse.of_success(StatusCodes.OK, result)
    except Exception as e:
        raise
