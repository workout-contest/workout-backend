"""
사용자 관련 라우터
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.schema.schemas import LoginRequest, SignupRequest, SignupResponse, TokenResponse, RefreshRequest, UserInfo, LogoutRequest, LogoutResponse
from app.base.base_response import BaseResponse
from app.core.database import get_db
from app.users.services.user_service import UserService
from app.core.constants import StatusCodes

logger = logging.getLogger(__name__)

router = APIRouter()

# UserService 인스턴스 생성
user_service = UserService()


@router.post(
    "/login",
    response_model=BaseResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="로그인",
    description="사용자 아이디와 비밀번호로 로그인하여 JWT 토큰을 발급받습니다.",
    tags=["인증"]
)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    로그인
    
    - **username**: 아이디
    - **password**: 비밀번호
    
    액세스 토큰과 리프레시 토큰이 발급됩니다.
    """
    try:
        result = await user_service.login(login_data.username, login_data.password, db)
        return BaseResponse.of_success(StatusCodes.OK, TokenResponse(**result))
    except Exception as e:
        raise


@router.post(
    "/signup", 
    response_model=BaseResponse[SignupResponse],
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="새로운 사용자를 등록합니다. 이름, 나이, 성별, 키, 몸무게를 입력받아 BMI를 계산합니다.",
    tags=["사용자"]
)
async def signup(signup_data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    회원가입

    - **username**: 아이디 (중복 불가)
    - **password**: 비밀번호
    - **name**: 사용자 이름
    - **age**: 나이
    - **gender**: 성별
    - **height**: 키 (cm)
    - **weight**: 몸무게 (kg)

    BMI가 자동으로 계산됩니다.
    """
    try:
        result = await user_service.signup(signup_data, db)
        return BaseResponse.of_success(StatusCodes.CREATED, result)
    except Exception as e:
        raise


@router.post(
    "/refresh", 
    response_model=BaseResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="토큰 갱신",
    description="리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급받습니다.",
    tags=["인증"]
)
async def refresh_token(request: RefreshRequest):
    """
    액세스 토큰 갱신
    
    - **refresh_token**: 유효한 리프레시 토큰
    
    새로운 액세스 토큰이 발급됩니다.
    """
    try:
        result = await user_service.refresh_access_token(request.refresh_token)
        return BaseResponse.of_success(StatusCodes.OK, result)
    except Exception as e:
        raise


@router.get(
    "/user/{user_id}", 
    response_model=BaseResponse[UserInfo],
    status_code=status.HTTP_200_OK,
    summary="사용자 정보 조회",
    description="사용자 ID로 사용자 정보를 조회합니다.",
    tags=["사용자"]
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    사용자 정보 조회
    
    - **user_id**: 조회할 사용자의 ID
    
    사용자의 상세 정보를 반환합니다.
    """
    try:
        result = await user_service.get_user_by_id(user_id, db)
        return BaseResponse.of_success(StatusCodes.OK, result)
    except Exception as e:
        raise


@router.post(
    "/logout",
    response_model=BaseResponse[LogoutResponse],
    status_code=status.HTTP_200_OK,
    summary="로그아웃",
    description="액세스 토큰과 리프레시 토큰을 블랙리스트에 추가하여 로그아웃을 처리합니다.",
    tags=["인증"]
)
async def logout(request: LogoutRequest):
    """
    로그아웃
    
    - **access_token**: 현재 사용 중인 액세스 토큰
    - **refresh_token**: 현재 사용 중인 리프레시 토큰
    
    두 토큰 모두 블랙리스트에 추가되어 더 이상 사용할 수 없게 됩니다.
    """
    try:
        result = await user_service.logout(request.access_token, request.refresh_token)
        return BaseResponse.of_success(StatusCodes.OK, LogoutResponse(**result))
    except Exception as e:
        raise
