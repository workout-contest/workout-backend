"""
사용자 서비스
"""
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.users.models.user import User
from app.users.schema.schemas import SignupRequest, SignupResponse, TokenResponse, UserInfo
from app.core.token_manager import TokenManager
from app.core.redis_manager import RedisManager
from app.core.exceptions import ConflictException, NotFoundException, ServerException, UnauthorizedException
from app.core.constants import ResponseMessages, TokenType
from app.core.utils import format_datetime, hash_password, verify_password

logger = logging.getLogger(__name__)


class UserService:
    """사용자 서비스 클래스"""
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.redis_manager = RedisManager()
        # 토큰 매니저에 Redis 매니저 설정
        self.token_manager.set_redis_manager(self.redis_manager)
    
    async def login(self, username: str, password: str, db: AsyncSession) -> Dict[str, str]:
        """
        로그인 처리
        
        Args:
            username: 사용자 아이디
            password: 비밀번호
            db: 데이터베이스 세션
            
        Returns:
            토큰 정보
            
        Raises:
            UnauthorizedException: 잘못된 인증 정보
            ServerException: 서버 오류
        """
        try:
            # 사용자 조회
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            
            if not user:
                raise UnauthorizedException("아이디 또는 비밀번호가 올바르지 않습니다.")
            
            # 비밀번호 검증
            if not verify_password(password, user.password):
                raise UnauthorizedException("아이디 또는 비밀번호가 올바르지 않습니다.")
            
            # 토큰 생성 및 저장
            tokens = await self._generate_and_store_tokens(user.id)
            
            return tokens
            
        except UnauthorizedException:
            logger.warning(f"로그인 실패: {username}")
            raise
        except Exception as e:
            logger.error(f"로그인 처리 실패: {e}")
            raise ServerException(f"로그인 처리 실패: {str(e)}")
    
    async def signup(self, signup_data: SignupRequest, db: AsyncSession) -> SignupResponse:
        """
        회원가입 처리
        
        Args:
            signup_data: 회원가입 요청 데이터
            db: 데이터베이스 세션
            
        Returns:
            회원가입 응답
            
        Raises:
            ConflictException: 중복된 회원 정보
            ServerException: 서버 오류
        """
        try:
            # BMI 계산
            bmi = signup_data.calculate_bmi()
            
            # 중복 체크
            await self._check_duplicate_user(signup_data.username, db)
            
            # 새 회원 생성
            new_user = await self._create_user(signup_data, bmi, db)
            
            return SignupResponse(
                message=ResponseMessages.SIGNUP_SUCCESS,
                user_id=new_user.id,
                bmi=new_user.bmi
            )
            
        except ConflictException:
            logger.warning(f"중복 회원가입 시도: {signup_data.name}")
            raise
        except Exception as e:
            logger.error(f"회원가입 처리 실패: {e}")
            await db.rollback()
            raise ServerException(f"회원가입 처리 실패: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        액세스 토큰 갱신
        
        Args:
            refresh_token: 리프레시 토큰
            
        Returns:
            토큰 응답
            
        Raises:
            UnauthorizedException: 유효하지 않은 토큰
            ServerException: 서버 오류
        """
        try:
            # 리프레시 토큰 검증
            payload = self.token_manager.verify_token(refresh_token)
            
            if payload.get("type") != TokenType.REFRESH:
                raise UnauthorizedException(ResponseMessages.INVALID_TOKEN)
            
            user_id = payload.get("user_id")
            
            # Redis에서 리프레시 토큰 확인
            await self._validate_refresh_token(user_id, refresh_token)
            
            # 새 액세스 토큰 생성
            new_access_token = self.token_manager.create_access_token(user_id)
            
            # Redis에 새 액세스 토큰 저장
            self.redis_manager.store_tokens(user_id, new_access_token, refresh_token)
            
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=refresh_token
            )
            
        except UnauthorizedException:
            logger.warning("유효하지 않은 리프레시 토큰")
            raise
        except Exception as e:
            logger.error(f"토큰 갱신 실패: {e}")
            raise ServerException(f"토큰 갱신 실패: {str(e)}")
    
    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> UserInfo:
        """
        ID로 회원 조회
        
        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션
            
        Returns:
            사용자 정보
            
        Raises:
            NotFoundException: 사용자를 찾을 수 없음
        """
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise NotFoundException(ResponseMessages.USER_NOT_FOUND)

            return UserInfo(
                id=user.id,
                username=user.username,
                name=user.name,
                age=user.age,
                gender=user.gender,
                height=user.height,
                weight=user.weight,
                bmi=user.bmi,
                created_at=format_datetime(user.created_at),
                updated_at=format_datetime(user.updated_at)
            )
            
        except NotFoundException:
            logger.warning(f"사용자를 찾을 수 없음: ID {user_id}")
            raise
        except Exception as e:
            logger.error(f"사용자 조회 실패: {e}")
            raise ServerException(f"사용자 조회 실패: {str(e)}")
    
    async def logout(self, access_token: str, refresh_token: str) -> Dict[str, str]:
        """
        로그아웃 처리
        
        Args:
            access_token: 액세스 토큰
            refresh_token: 리프레시 토큰
            
        Returns:
            로그아웃 응답 메시지
            
        Raises:
            UnauthorizedException: 유효하지 않은 토큰
            ServerException: 서버 오류
        """
        try:
            # 액세스 토큰 검증
            access_payload = self.token_manager.verify_token(access_token)
            if access_payload.get("type") != TokenType.ACCESS:
                raise UnauthorizedException(ResponseMessages.INVALID_TOKEN)
            
            # 리프레시 토큰 검증
            refresh_payload = self.token_manager.verify_token(refresh_token)
            if refresh_payload.get("type") != TokenType.REFRESH:
                raise UnauthorizedException(ResponseMessages.INVALID_TOKEN)
            
            user_id = access_payload.get("user_id")
            
            # 토큰 만료 시간 계산
            access_expire_seconds = self.token_manager.access_token_expire_minutes * 60
            refresh_expire_seconds = self.token_manager.refresh_token_expire_days * 24 * 60 * 60
            
            # 토큰을 블랙리스트에 추가
            self.redis_manager.add_to_blacklist(access_token, access_expire_seconds)
            self.redis_manager.add_to_blacklist(refresh_token, refresh_expire_seconds)
            
            # Redis에서 사용자 토큰 삭제
            self.redis_manager.delete_tokens(user_id)
            
            return {"message": "로그아웃이 완료되었습니다."}
            
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"로그아웃 처리 실패: {e}")
            raise ServerException(f"로그아웃 처리 실패: {str(e)}")
    
    async def _check_duplicate_user(self, username: str, db: AsyncSession) -> None:
        """중복 사용자 체크"""
        # 아이디 중복 체크
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ConflictException(ResponseMessages.DUPLICATE_USER)
    
    async def _create_user(self, signup_data: SignupRequest, bmi: float, db: AsyncSession) -> User:
        """사용자 생성"""
        # 비밀번호 해싱
        hashed_password = hash_password(signup_data.password)
        
        new_user = User(
            username=signup_data.username,
            password=hashed_password,
            name=signup_data.name,
            age=signup_data.age,
            gender=signup_data.gender,
            height=signup_data.height,
            weight=signup_data.weight,
            bmi=bmi
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
    
    async def _generate_and_store_tokens(self, user_id: int) -> Dict[str, str]:
        """토큰 생성 및 저장"""
        access_token = self.token_manager.create_access_token(user_id)
        refresh_token = self.token_manager.create_refresh_token(user_id)
        
        # Redis에 토큰 저장
        self.redis_manager.store_tokens(user_id, access_token, refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    async def _validate_refresh_token(self, user_id: int, refresh_token: str) -> None:
        """리프레시 토큰 유효성 검사"""
        stored_refresh_token = self.redis_manager.get_refresh_token(user_id)
        if stored_refresh_token != refresh_token:
            raise UnauthorizedException(ResponseMessages.INVALID_TOKEN)
