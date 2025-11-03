"""
식단 관련 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class MealInfo(BaseModel):
    """식사 정보"""
    meal_type: str = Field(..., description="식사 타입 (breakfast, lunch, dinner, snack)")
    food_name: str = Field(..., description="음식 이름")
    calories: float = Field(..., description="칼로리")


class DailyDietRequest(BaseModel):
    """일별 식단 요청"""
    day: int = Field(..., description="일 (1-31)")
    meals: List[MealInfo] = Field(..., description="식사 정보 목록")


class MonthlyDietRequest(BaseModel):
    """월별 식단 요청"""
    daily_diets: List[DailyDietRequest] = Field(..., description="일별 식단 정보 목록")
    year: int = Field(..., description="년도")
    month: int = Field(..., description="월")


class DietResponse(BaseModel):
    """식단 저장 응답"""
    message: str = Field(..., description="응답 메시지")
    user_id: int = Field(..., description="사용자 ID")
    year: int = Field(..., description="년도")
    month: int = Field(..., description="월")
    saved_days: int = Field(..., description="저장된 일수")
    total_meals: int = Field(..., description="총 식사 수")
    daily_summary: Dict[int, List[MealInfo]] = Field(..., description="일별 식단 요약")


class DietInfo(BaseModel):
    """식단 정보"""
    id: int = Field(..., description="식단 ID")
    user_id: int = Field(..., description="사용자 ID")
    food_name: str = Field(..., description="음식 이름")
    calories: float = Field(..., description="칼로리")
    meal_type: str = Field(..., description="식사 타입")
    year: int = Field(..., description="년도")
    month: int = Field(..., description="월")
    day: int = Field(..., description="일")
    created_at: str = Field(..., description="생성일시")
    updated_at: str = Field(..., description="수정일시")
