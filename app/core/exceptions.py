from typing import Optional


class BaseAPIException(Exception):
    def __init__(
            self,
            status_code: int,
            custom_code: str,
            message: str,
            details: Optional[dict] = None
    ):
        self.status_code = status_code
        self.custom_code = custom_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class BadRequestException(BaseAPIException):
    def __init__(self, message: str = "잘못된 요청입니다.", details: Optional[dict] = None):
        super().__init__(
            status_code=400,
            custom_code="BAD_REQUEST",
            message=message,
            details=details
        )


class ConflictException(BaseAPIException):
    def __init__(self, message: str = "리소스 충돌이 발생했습니다.", details: Optional[dict] = None):
        super().__init__(
            status_code=409,
            custom_code="CONFLICT",
            message=message,
            details=details
        )


class NotFoundException(BaseAPIException):
    def __init__(self, message: str = "리소스를 찾을 수 없습니다.", details: Optional[dict] = None):
        super().__init__(
            status_code=404,
            custom_code="NOT_FOUND",
            message=message,
            details=details
        )


class ServerException(BaseAPIException):
    def __init__(self, message: str = "내부 서버 오류가 발생했습니다.", details: Optional[dict] = None):
        super().__init__(
            status_code=500,
            custom_code="SERVER",
            message=message,
            details=details
        )


class UnauthorizedException(BaseAPIException):
    def __init__(self, message: str = "인증이 필요합니다.", details: Optional[dict] = None):
        super().__init__(
            status_code=401,
            custom_code="UNAUTHORIZED",
            message=message,
            details=details
        )
