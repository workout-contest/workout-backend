"""
운동 관련 라우터
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.workouts.schema.schemas import MonthlyWorkoutRequest, WorkoutResponse, WorkoutInfo, WorkoutProgramInfo
from app.workouts.schema.prescription_schemas import PrescriptionResponse, PrescriptionCandidate
from app.base.base_response import BaseResponse
from app.core.database import get_db
from app.workouts.services.workout_service import WorkoutService
from app.workouts.services.workout_program_service import WorkoutProgramService
from app.workouts.services.prescription_service import get_prescription_service
from app.users.services.user_service import UserService
from app.core.constants import StatusCodes

logger = logging.getLogger(__name__)

router = APIRouter()

# WorkoutService 인스턴스 생성
workout_service = WorkoutService()
workout_program_service = WorkoutProgramService()
user_service = UserService()
# prescription_service는 필요할 때마다 가져오도록 함 (모델 로드 시점 문제 방지)


@router.post(
    "/workout/{user_id}",
    response_model=BaseResponse[WorkoutResponse],
    status_code=status.HTTP_201_CREATED,
    summary="월별 운동 정보 저장",
    description="특정 사용자의 월별 운동 정보를 저장합니다. 해당 연월의 기존 데이터는 모두 삭제되고 새 데이터로 교체됩니다.",
    tags=["운동"]
)
async def save_workout(user_id: int, workout_data: MonthlyWorkoutRequest, db: AsyncSession = Depends(get_db)):
    """
    월별 운동 정보 저장
    
    - **user_id**: 사용자 ID
    - **daily_workouts**: 일별 운동 정보 목록
      - **day**: 일 (1-31)
      - **workout_names**: 해당 일의 운동 이름 목록 (1-10개)
    - **year**: 년도 (2020-2030)
    - **month**: 월 (1-12)
    
    해당 사용자의 해당 연월에 기존에 저장된 모든 운동 데이터가 삭제되고, 새로 전송된 데이터로 교체됩니다.
    """
    try:
        result = await workout_service.save_workout(user_id, workout_data, db)
        return BaseResponse.of_success(StatusCodes.CREATED, result)
    except Exception as e:
        raise


@router.get(
    "/workout/{user_id}",
    response_model=BaseResponse[List[WorkoutInfo]],
    status_code=status.HTTP_200_OK,
    summary="사용자 운동 정보 조회",
    description="특정 사용자의 운동 정보를 조회합니다. 년도와 월로 필터링 가능합니다.",
    tags=["운동"]
)
async def get_user_workouts(
    user_id: int, 
    year: Optional[int] = Query(None, ge=2020, le=2030, description="년도"),
    month: Optional[int] = Query(None, ge=1, le=12, description="월"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 운동 정보 조회
    
    - **user_id**: 사용자 ID
    - **year**: 년도 (선택사항, 2020-2030)
    - **month**: 월 (선택사항, 1-12)
    
    년도와 월을 지정하지 않으면 모든 운동 정보를 반환합니다.
    """
    try:
        result = await workout_service.get_user_workouts(user_id, year, month, db)
        return BaseResponse.of_success(StatusCodes.OK, result)
    except Exception as e:
        raise


@router.get(
    "/workout-program",
    response_model=BaseResponse[List[WorkoutProgramInfo]],
    status_code=status.HTTP_200_OK,
    summary="운동 프로그램 조회",
    description="소분류(category_small)를 파라미터로 받아 해당하는 운동 프로그램 목록을 조회합니다.",
    tags=["운동 프로그램"]
)
async def get_workout_programs_by_category_small(
    category_small: str = Query(..., description="소분류"),
    db: AsyncSession = Depends(get_db)
):
    """
    소분류로 운동 프로그램 조회
    
    - **category_small**: 소분류 (필수)
    
    해당 소분류에 속하는 모든 운동 프로그램을 반환합니다.
    """
    try:
        result = await workout_program_service.get_programs_by_category_small(category_small, db)
        return BaseResponse.of_success(StatusCodes.OK, result)
    except Exception as e:
        raise


@router.get(
    "/prescription/recommend/{user_seq}",
    response_model=BaseResponse[List[PrescriptionCandidate]],
    status_code=status.HTTP_200_OK,
    summary="사용자 기반 AI 처방 추천",
    description="사용자 시퀀스(user_seq)를 기반으로 해당 사용자의 키와 몸무게를 가져와 AI 모델로 개인 맞춤형 운동 처방을 추천합니다.",
    tags=["처방 추천"]
)
async def recommend_prescription_by_user_seq(
    user_seq: int,
    top_k: Optional[int] = Query(3, ge=1, le=10, description="상위 추천 개수"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 기반 AI 처방 추천
    
    - **user_seq**: 사용자 시퀀스 (사용자 ID)
    - **top_k**: 상위 추천 개수 (선택사항, 기본값: 3)
    
    해당 사용자의 키와 몸무게 정보를 바탕으로 최적의 운동 처방을 추천합니다.
    """
    try:
        # 사용자 정보 조회
        user = await user_service.get_user_by_id(user_seq, db)
        
        # 처방 추천 서비스 가져오기 (매번 새로 가져와서 모델이 최신 상태인지 확인)
        prescription_service = get_prescription_service()
        
        # 처방 추천
        result = prescription_service.predict_prescription(
            height_cm=user.height,
            weight_kg=user.weight,
            top_k=top_k,
            conf_thr=0.55
        )
        return BaseResponse.of_success(StatusCodes.OK, result)
    except Exception as e:
        logger.error(f"사용자 기반 처방 추천 실패: {e}")
        raise
