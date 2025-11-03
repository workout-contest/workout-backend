"""
유틸리티 함수들
"""
import hashlib
import logging
import bcrypt
from typing import Optional
from datetime import datetime
from app.core.constants import BMICategory

logger = logging.getLogger(__name__)


def calculate_bmi(height: float, weight: float) -> float:
    """
    BMI 계산
    
    Args:
        height: 키 (cm)
        weight: 몸무게 (kg)
        
    Returns:
        BMI 값 (소수점 1자리)
        
    Raises:
        ValueError: 키가 0 이하일 때
    """
    if height <= 0:
        raise ValueError("키는 0보다 커야 합니다")
    
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    return round(bmi, 1)


def get_bmi_category(bmi: float) -> str:
    """
    BMI 분류 반환
    
    Args:
        bmi: BMI 값
        
    Returns:
        BMI 분류 문자열
    """
    if bmi < 18.5:
        return BMICategory.UNDERWEIGHT
    elif 18.5 <= bmi < 23:
        return BMICategory.NORMAL
    elif 23 <= bmi < 25:
        return BMICategory.OVERWEIGHT
    else:
        return BMICategory.OBESE


def generate_unique_key(name: str, age: int, gender: str, height: float, weight: float) -> str:
    """
    복합 유니크키 생성
    
    Args:
        name: 이름
        age: 나이
        gender: 성별
        height: 키
        weight: 몸무게
        
    Returns:
        SHA256 해시값
    """
    key_string = f"{name}_{age}_{gender}_{height}_{weight}"
    return hashlib.sha256(key_string.encode()).hexdigest()


def validate_user_data(name: str, age: int, gender: str, height: float, weight: float) -> None:
    """
    사용자 데이터 유효성 검사
    
    Args:
        name: 이름
        age: 나이
        gender: 성별
        height: 키
        weight: 몸무게
        
    Raises:
        ValueError: 유효하지 않은 데이터일 때
    """
    if not name or len(name.strip()) == 0:
        raise ValueError("이름은 필수입니다")
    
    if age < 1 or age > 150:
        raise ValueError("나이는 1-150 사이여야 합니다")
    
    if gender.lower() not in ["male", "female"]:
        raise ValueError("성별은 male 또는 female이어야 합니다")
    
    if height <= 0 or height > 300:
        raise ValueError("키는 1-300cm 사이여야 합니다")
    
    if weight <= 0 or weight > 500:
        raise ValueError("몸무게는 1-500kg 사이여야 합니다")


def format_datetime(dt: datetime) -> str:
    """
    날짜시간 포맷팅
    
    Args:
        dt: 날짜시간 객체
        
    Returns:
        포맷된 문자열
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def safe_int(value: Optional[str], default: int = 0) -> int:
    """
    안전한 정수 변환
    
    Args:
        value: 변환할 값
        default: 기본값
        
    Returns:
        변환된 정수값
    """
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        logger.warning(f"정수 변환 실패: {value}, 기본값 사용: {default}")
        return default


def hash_password(password: str) -> str:
    """
    비밀번호 해싱
    
    Args:
        password: 원본 비밀번호
        
    Returns:
        해싱된 비밀번호
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        password: 원본 비밀번호
        hashed_password: 해싱된 비밀번호
        
    Returns:
        비밀번호 일치 여부
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def safe_float(value: Optional[str], default: float = 0.0) -> float:
    """
    안전한 실수 변환
    
    Args:
        value: 변환할 값
        default: 기본값
        
    Returns:
        변환된 실수값
    """
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        logger.warning(f"실수 변환 실패: {value}, 기본값 사용: {default}")
        return default
