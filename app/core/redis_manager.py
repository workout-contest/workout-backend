import redis
from typing import Optional
import logging
from config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    def __init__(self):
        self.use_redis = settings.use_redis
        
        if not self.use_redis:
            self.redis_client = None
            return
            
        self.redis_host = settings.redis_host
        self.redis_port = settings.redis_port
        self.redis_db = settings.redis_db
        self.redis_password = settings.redis_password
        
        try:
            # Redis 연결 설정
            redis_config = {
                "host": self.redis_host,
                "port": self.redis_port,
                "db": self.redis_db,
                "decode_responses": True,
                "socket_connect_timeout": 5,  # 연결 타임아웃
                "socket_timeout": 5,  # 소켓 타임아웃
            }
            
            # 비밀번호가 설정되어 있을 때만 추가
            if self.redis_password:
                redis_config["password"] = self.redis_password
            
            self.redis_client = redis.Redis(**redis_config)
            
            # 연결 테스트
            self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            self.redis_client = None
    
    def store_tokens(self, user_id: int, access_token: str, refresh_token: str):
        """토큰을 Redis에 저장"""
        if not self.redis_client:
            return
            
        try:
            # 액세스 토큰 저장 (30분)
            self.redis_client.setex(
                f"access_token:{user_id}",
                30 * 60,  # 30분
                access_token
            )
            
            # 리프레시 토큰 저장 (7일)
            self.redis_client.setex(
                f"refresh_token:{user_id}",
                7 * 24 * 60 * 60,  # 7일
                refresh_token
            )
            
        except Exception as e:
            logger.error(f"토큰 저장 실패: {e}")
            raise
    
    def get_access_token(self, user_id: int) -> Optional[str]:
        """액세스 토큰 조회"""
        if not self.redis_client:
            return None
            
        try:
            return self.redis_client.get(f"access_token:{user_id}")
        except Exception as e:
            logger.error(f"액세스 토큰 조회 실패: {e}")
            return None
    
    def get_refresh_token(self, user_id: int) -> Optional[str]:
        """리프레시 토큰 조회"""
        if not self.redis_client:
            return None
            
        try:
            return self.redis_client.get(f"refresh_token:{user_id}")
        except Exception as e:
            logger.error(f"리프레시 토큰 조회 실패: {e}")
            return None
    
    def delete_tokens(self, user_id: int):
        """토큰 삭제"""
        if not self.redis_client:
            return
            
        try:
            self.redis_client.delete(f"access_token:{user_id}")
            self.redis_client.delete(f"refresh_token:{user_id}")
        except Exception as e:
            logger.error(f"토큰 삭제 실패: {e}")
    
    def add_to_blacklist(self, token: str, expire_seconds: int):
        """토큰을 블랙리스트에 추가"""
        if not self.redis_client:
            return
            
        try:
            self.redis_client.setex(f"blacklist:{token}", expire_seconds, "1")
        except Exception as e:
            logger.error(f"블랙리스트 추가 실패: {e}")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """토큰이 블랙리스트에 있는지 확인"""
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.exists(f"blacklist:{token}") > 0
        except Exception as e:
            logger.error(f"블랙리스트 확인 실패: {e}")
            return False