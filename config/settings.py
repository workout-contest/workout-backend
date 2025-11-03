import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class Settings:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.active_profile = self._get_active_profile()
        self._load_environment_config()
    
    def _get_active_profile(self) -> str:
        profile = os.getenv('ACTIVE_PROFILE')
        if profile:
            return profile
        
        default_env_path = self.base_dir / 'default.env'
        if default_env_path.exists():
            load_dotenv(default_env_path)
            profile = os.getenv('ACTIVE_PROFILE')
            if profile:
                return profile
        
        return 'local'
    
    def _load_environment_config(self):
        env_file = self.base_dir / f'{self.active_profile}.env'
        
        if env_file.exists():
            load_dotenv(env_file)
        else:
            raise FileNotFoundError(f"환경 설정 파일을 찾을 수 없습니다: {env_file}")
    
    @property
    def database_url(self) -> str:
        url = os.getenv('DATABASE_URL')
        if not url:
            raise ValueError(f"DATABASE_URL이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return url
    
    @property
    def debug(self) -> bool:
        debug = os.getenv('DEBUG')
        if debug is None:
            raise ValueError(f"DEBUG가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return debug.lower() in ('true', '1', 'yes')
    
    @property
    def log_level(self) -> str:
        level = os.getenv('LOG_LEVEL')
        if not level:
            raise ValueError(f"LOG_LEVEL이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return level
    
    # JWT 설정
    @property
    def jwt_secret_key(self) -> str:
        key = os.getenv('JWT_SECRET_KEY')
        if not key:
            raise ValueError(f"JWT_SECRET_KEY가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return key
    
    @property
    def jwt_algorithm(self) -> str:
        algorithm = os.getenv('JWT_ALGORITHM')
        if not algorithm:
            raise ValueError(f"JWT_ALGORITHM이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return algorithm
    
    @property
    def access_token_expire_minutes(self) -> int:
        minutes = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
        if not minutes:
            raise ValueError(f"ACCESS_TOKEN_EXPIRE_MINUTES이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return int(minutes)
    
    @property
    def refresh_token_expire_days(self) -> int:
        days = os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')
        if not days:
            raise ValueError(f"REFRESH_TOKEN_EXPIRE_DAYS가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return int(days)
    
    # Redis 설정
    @property
    def use_redis(self) -> bool:
        use_redis = os.getenv('USE_REDIS')
        if use_redis is None:
            raise ValueError(f"USE_REDIS가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return use_redis.lower() in ('true', '1', 'yes')
    
    @property
    def redis_host(self) -> str:
        host = os.getenv('REDIS_HOST')
        if not host:
            raise ValueError(f"REDIS_HOST가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return host
    
    @property
    def redis_port(self) -> int:
        port = os.getenv('REDIS_PORT')
        if not port:
            raise ValueError(f"REDIS_PORT가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return int(port)
    
    @property
    def redis_db(self) -> int:
        db = os.getenv('REDIS_DB')
        if not db:
            raise ValueError(f"REDIS_DB가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return int(db)
    
    @property
    def redis_password(self) -> Optional[str]:
        return os.getenv('REDIS_PASSWORD')  # 선택적 값
    
    # CORS 설정
    @property
    def cors_origins(self) -> list:
        """CORS 허용 오리진 목록"""
        origins = os.getenv('CORS_ORIGINS')
        if not origins:
            raise ValueError(f"CORS_ORIGINS가 설정되지 않았습니다. ({self.active_profile} 환경)")
        if origins == '*':
            return ["*"]
        return [origin.strip() for origin in origins.split(',')]
    
    @property
    def cors_allow_credentials(self) -> bool:
        """CORS 자격 증명 허용"""
        allow = os.getenv('CORS_ALLOW_CREDENTIALS')
        if allow is None:
            raise ValueError(f"CORS_ALLOW_CREDENTIALS가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return allow.lower() in ('true', '1', 'yes')
    
    # 공공데이터 API 설정
    @property
    def public_data_api_key(self) -> str:
        """공공데이터포털 API 인증키 (인코딩된 형태를 그대로 사용)"""
        key = os.getenv('PUBLIC_DATA_API_KEY')
        if not key:
            raise ValueError(f"PUBLIC_DATA_API_KEY가 설정되지 않았습니다. ({self.active_profile} 환경)")
        return key
    
    @property
    def public_data_api_base_url(self) -> str:
        """공공데이터포털 API Base URL"""
        url = os.getenv('PUBLIC_DATA_API_BASE_URL')
        if not url:
            raise ValueError(f"PUBLIC_DATA_API_BASE_URL이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return url
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)
    
    def __str__(self):
        return f"Settings(profile={self.active_profile}, debug={self.debug})"
