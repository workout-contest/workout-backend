"""
사용자 관련 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.core.utils import calculate_bmi


class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str = Field(..., description="아이디")
    password: str = Field(..., description="비밀번호")


class SignupRequest(BaseModel):
    """회원가입 요청"""
    username: str = Field(..., description="아이디")
    password: str = Field(..., description="비밀번호")
    name: str = Field(..., description="이름")
    age: int = Field(..., description="나이")
    gender: str = Field(..., description="성별")
    height: float = Field(..., description="키 (cm)")
    weight: float = Field(..., description="몸무게 (kg)")

    def calculate_bmi(self) -> float:
        """BMI 계산"""
        return calculate_bmi(self.height, self.weight)


class SignupResponse(BaseModel):
    """회원가입 응답"""
    message: str = Field(..., description="응답 메시지")
    user_id: int = Field(..., description="사용자 ID")
    bmi: float = Field(..., description="BMI 값")


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")


class RefreshRequest(BaseModel):
    """리프레시 토큰 요청"""
    refresh_token: str = Field(..., min_length=1, description="리프레시 토큰")


class UserInfo(BaseModel):
    """사용자 정보"""
    id: int = Field(..., description="사용자 ID")
    username: str = Field(..., description="아이디")
    name: str = Field(..., description="이름")
    age: int = Field(..., description="나이")
    gender: str = Field(..., description="성별")
    height: float = Field(..., description="키 (cm)")
    weight: float = Field(..., description="몸무게 (kg)")
    bmi: float = Field(..., description="BMI 값")
    created_at: str = Field(..., description="생성일시")
    updated_at: str = Field(..., description="수정일시")


class LogoutRequest(BaseModel):
    """로그아웃 요청"""
    access_token: str = Field(..., min_length=1, description="액세스 토큰")
    refresh_token: str = Field(..., min_length=1, description="리프레시 토큰")


class LogoutResponse(BaseModel):
    """로그아웃 응답"""
    message: str = Field(..., description="응답 메시지")
