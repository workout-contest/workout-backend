"""
애플리케이션 팩토리
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from app.core.middleware import setup_exception_handlers
from app.users.routers.router import router as user_router
from app.workouts.routers.router import router as workout_router
from app.diets.routers.router import router as diet_router
from app.core.auto_migration import auto_update_schema
from app.users.models.user import User  # 모델 등록을 위해 임포트
from app.workouts.models.workout import Workout  # 모델 등록을 위해 임포트
from app.workouts.models.workout_program import WorkoutProgram  # 모델 등록을 위해 임포트
from app.workouts.models.physical_fitness_result import PhysicalFitnessResult  # 모델 등록을 위해 임포트
from app.diets.models.diet import Diet  # 모델 등록을 위해 임포트

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    
    app = FastAPI(
        title="Workout Backend API",
        description=f"Workout Backend API - {settings.active_profile.upper()} Environment",
        debug=settings.debug,
        version="1.0.0",
    )
    
    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],  # 모든 HTTP 메서드 허용
        allow_headers=["*"],  # 모든 헤더 허용
    )
    
    # 예외 핸들러 설정
    setup_exception_handlers(app)
    
    # 라우터 등록
    app.include_router(user_router)
    app.include_router(workout_router)
    app.include_router(diet_router)
    
    # 헬스 체크 엔드포인트
    from fastapi import status
    from app.base.base_response import BaseResponse
    
    @app.get("/actuator/health", response_model=BaseResponse[dict], status_code=status.HTTP_200_OK)
    async def health_check():
        health_data = {"status": "healthy", "environment": settings.active_profile}
        return BaseResponse.of_success(status.HTTP_200_OK, health_data)
    
    # 시작 이벤트
    @app.on_event("startup")
    async def startup_event():
        logger.info("서버 시작 이벤트 실행 중...")
        await auto_update_schema()
        logger.info("데이터베이스 스키마 업데이트 완료")
        
        # CSV 데이터 로딩 (이미 있으면 스킵)
        logger.info("=" * 80)
        logger.info("운동 프로그램 CSV 데이터 로딩 시작")
        logger.info("=" * 80)
        from app.workouts.services.workout_program_service import load_workout_programs_from_csv
        try:
            saved, skipped = await load_workout_programs_from_csv()
            if saved > 0:
                logger.info(f"✓ 운동 프로그램 데이터 로딩 완료: {saved}개 저장, {skipped}개 스킵")
            else:
                logger.info(f"✓ 운동 프로그램 데이터: 모든 데이터가 이미 존재함 (스킵: {skipped}개)")
        except Exception as e:
            logger.error(f"✗ 운동 프로그램 데이터 로딩 중 오류 발생: {e}")
            logger.exception(e)
        
        # 공공데이터 API 데이터 로딩 (이미 있으면 스킵, 전체 데이터 수집)
        logger.info("")
        logger.info("=" * 80)
        logger.info("체력 측정 결과 공공데이터 API 로딩 시작 (전체 데이터)")
        logger.info("=" * 80)
        from app.workouts.services.physical_fitness_service import load_physical_fitness_data_from_api
        try:
            saved, skipped = await load_physical_fitness_data_from_api(max_pages=None)
            logger.info("")
            logger.info(f"✓ 체력 측정 결과 데이터 로딩 완료: {saved}개 저장, {skipped}개 스킵")
        except Exception as e:
            logger.error(f"✗ 체력 측정 결과 데이터 로딩 중 오류 발생: {e}")
            logger.exception(e)
        
        # 모델 학습 (모델 파일이 없으면 자동 학습)
        logger.info("")
        logger.info("=" * 80)
        logger.info("처방 추천 모델 확인 및 학습")
        logger.info("=" * 80)
        from pathlib import Path
        model_dir = Path(__file__).parent.parent.parent / "models"
        model_path = model_dir / "prescriptor_model.joblib"
        encoder_path = model_dir / "prescriptor_label_encoder.joblib"
        meta_path = model_dir / "prescriptor_meta.json"
        
        if not model_path.exists() or not encoder_path.exists() or not meta_path.exists():
            logger.info("모델 파일이 없습니다. 모델 학습을 시작합니다...")
            from app.workouts.services.train_prescription_model import train_model
            try:
                await train_model()
                logger.info("✓ 모델 학습 완료")
                # 모델 학습 완료 후 PrescriptionService 재로드
                from app.workouts.services.prescription_service import reload_prescription_service
                reload_prescription_service()
                logger.info("✓ 모델 서비스 재로드 완료")
            except Exception as e:
                logger.error(f"✗ 모델 학습 중 오류 발생: {e}")
                logger.exception(e)
        else:
            logger.info("✓ 모델 파일이 이미 존재합니다. 학습을 건너뜁니다.")
            # 모델 파일이 있어도 서비스에 모델이 로드되지 않았을 수 있으므로 재로드 시도
            from app.workouts.services.prescription_service import get_prescription_service
            service = get_prescription_service()
            if not service.model_loaded:
                logger.info("모델 서비스에 모델이 로드되지 않았습니다. 재로드 중...")
                service._load_model()
                if service.model_loaded:
                    logger.info("✓ 모델 서비스 로드 완료")
                else:
                    logger.warning("⚠ 모델 서비스 로드 실패 (API 사용 불가)")
        
        logger.info("서버 시작 완료")
    
    return app
