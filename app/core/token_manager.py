import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Dict, Any
from config import settings


class TokenManager:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
        self.redis_manager = None  # 나중에 설정
    
    def set_redis_manager(self, redis_manager):
        """Redis 매니저 설정"""
        self.redis_manager = redis_manager
    
    def create_access_token(self, user_id: int) -> str:
        """액세스 토큰 생성"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int) -> str:
        """리프레시 토큰 생성"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """토큰 검증 (블랙리스트 확인 포함)"""
        try:
            # 블랙리스트 확인
            if self.redis_manager and self.redis_manager.is_token_blacklisted(token):
                raise HTTPException(status_code=401, detail="로그아웃된 토큰입니다.")
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
