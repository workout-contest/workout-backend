"""
운동 정보 스키마
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime


class DailyWorkoutRequest(BaseModel):
    """일별 운동 정보"""
    day: int = Field(..., ge=1, le=31, description="일")
    workout_names: List[str] = Field(..., min_items=1, max_items=10, description="해당 일의 운동 이름 목록")

    @validator('workout_names')
    def validate_workout_names(cls, v):
        if not v:
            raise ValueError('운동 이름 목록은 필수입니다')
        
        # 각 운동 이름 검증
        validated_names = []
        for name in v:
            if not name or not name.strip():
                raise ValueError('운동 이름은 빈 값일 수 없습니다')
            validated_names.append(name.strip())
        
        # 중복 제거
        unique_names = list(set(validated_names))
        if len(unique_names) != len(validated_names):
            raise ValueError('중복된 운동 이름이 있습니다')
        
        return unique_names


class MonthlyWorkoutRequest(BaseModel):
    """월별 운동 정보 저장 요청"""
    daily_workouts: List[DailyWorkoutRequest] = Field(..., min_items=1, max_items=31, description="일별 운동 정보 목록")
    year: int = Field(..., ge=2020, le=2030, description="년도")
    month: int = Field(..., ge=1, le=12, description="월")

    @validator('daily_workouts')
    def validate_daily_workouts(cls, v):
        if not v:
            raise ValueError('일별 운동 정보는 필수입니다')
        
        # 일 중복 체크
        days = [workout.day for workout in v]
        if len(days) != len(set(days)):
            raise ValueError('중복된 일이 있습니다')
        
        return v


class WorkoutResponse(BaseModel):
    """운동 정보 저장 응답"""
    message: str = Field(..., description="응답 메시지")
    user_id: int = Field(..., description="사용자 ID")
    year: int = Field(..., description="년도")
    month: int = Field(..., description="월")
    saved_days: int = Field(..., description="저장된 일수")
    total_workouts: int = Field(..., description="총 저장된 운동 개수")
    daily_summary: Dict[int, List[str]] = Field(..., description="일별 저장된 운동 요약")


class WorkoutInfo(BaseModel):
    """운동 정보"""
    id: int = Field(..., description="운동 ID")
    user_id: int = Field(..., description="사용자 ID")
    workout_name: str = Field(..., description="운동 이름")
    year: int = Field(..., description="년도")
    month: int = Field(..., description="월")
    day: int = Field(..., description="일")
    created_at: str = Field(..., description="생성일시")
    updated_at: str = Field(..., description="수정일시")


class WorkoutProgramInfo(BaseModel):
    """운동 프로그램 정보"""
    id: int = Field(..., description="프로그램 ID")
    program_number: int = Field(..., description="프로그램 번호")
    category_large: str = Field(..., description="대분류")
    category_medium: str = Field(..., description="중분류")
    category_small: str = Field(..., description="소분류")
    title: str = Field(..., description="제목")
    video_url: str = Field(..., description="동영상 주소")
    created_at: str = Field(..., description="생성일시")
    updated_at: str = Field(..., description="수정일시")
