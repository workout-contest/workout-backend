from fastapi import Request
from fastapi.responses import JSONResponse
from app.base.base_response import BaseResponse
from app.core.exceptions import BaseAPIException
import logging

logger = logging.getLogger(__name__)


def setup_exception_handlers(app):
    """예외 핸들러 설정"""
    
    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
        """커스텀 API 예외 핸들러"""
        logger.error(f"API Exception: {exc.custom_code} - {exc.message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=BaseResponse.of_fail(exc.status_code, exc.message).dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """일반 예외 핸들러"""
        logger.error(f"Unexpected Error: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content=BaseResponse.of_fail(500, "예상치 못한 오류가 발생했습니다.").dict()
        )
