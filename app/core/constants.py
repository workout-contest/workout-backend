"""
공통 상수 및 설정
"""
from enum import Enum
from typing import Final

# API 응답 메시지
class ResponseMessages:
    SUCCESS: Final[str] = "SUCCESS"
    ERROR: Final[str] = "ERROR"
    SIGNUP_SUCCESS: Final[str] = "회원가입이 완료되었습니다."
    USER_NOT_FOUND: Final[str] = "회원을 찾을 수 없습니다."
    DUPLICATE_USER: Final[str] = "이미 사용 중인 아이디입니다."
    INVALID_TOKEN: Final[str] = "유효하지 않은 토큰입니다."
    TOKEN_EXPIRED: Final[str] = "토큰이 만료되었습니다."

# HTTP 상태 코드
class StatusCodes:
    OK: Final[int] = 200
    CREATED: Final[int] = 201
    BAD_REQUEST: Final[int] = 400
    UNAUTHORIZED: Final[int] = 401
    CONFLICT: Final[int] = 409
    INTERNAL_SERVER_ERROR: Final[int] = 500

# 토큰 타입
class TokenType:
    ACCESS: Final[str] = "access"
    REFRESH: Final[str] = "refresh"

# 성별
class Gender:
    MALE: Final[str] = "male"
    FEMALE: Final[str] = "female"

# BMI 분류
class BMICategory:
    UNDERWEIGHT: Final[str] = "저체중"
    NORMAL: Final[str] = "정상체중"
    OVERWEIGHT: Final[str] = "과체중"
    OBESE: Final[str] = "비만"
