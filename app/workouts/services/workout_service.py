"""
운동 서비스
"""
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from app.workouts.models.workout import Workout
from app.workouts.schema.schemas import MonthlyWorkoutRequest, WorkoutResponse, WorkoutInfo
from app.core.exceptions import ConflictException, NotFoundException, ServerException
from app.core.constants import ResponseMessages
from app.core.utils import format_datetime

logger = logging.getLogger(__name__)


class WorkoutService:
    """운동 서비스 클래스"""

    async def save_workout(self, user_id: int, workout_data: MonthlyWorkoutRequest, db: AsyncSession) -> WorkoutResponse:
        """
        월별 운동 정보 저장 (기존 데이터 삭제 후 새로 저장)

        Args:
            user_id: 사용자 ID
            workout_data: 월별 운동 정보 요청 데이터
            db: 데이터베이스 세션

        Returns:
            운동 정보 저장 응답

        Raises:
            ServerException: 서버 오류
        """
        try:
            # 해당 user_id와 연월의 기존 데이터 모두 삭제
            await self._delete_existing_workouts(user_id, workout_data.year, workout_data.month, db)
            
            daily_summary = {}
            total_workouts = 0
            
            # 각 일별로 운동 저장
            for daily_workout in workout_data.daily_workouts:
                saved_workouts = []
                
                # 해당 일의 각 운동 저장
                for workout_name in daily_workout.workout_names:
                    # 새 운동 정보 생성
                    new_workout = Workout(
                        user_id=user_id,
                        workout_name=workout_name,
                        year=workout_data.year,
                        month=workout_data.month,
                        day=daily_workout.day
                    )
                    
                    db.add(new_workout)
                    saved_workouts.append(workout_name)
                    total_workouts += 1
                
                daily_summary[daily_workout.day] = saved_workouts
            
            await db.commit()

            return WorkoutResponse(
                message=f"{len(workout_data.daily_workouts)}일, 총 {total_workouts}개의 운동 정보가 저장되었습니다.",
                user_id=user_id,
                year=workout_data.year,
                month=workout_data.month,
                saved_days=len(workout_data.daily_workouts),
                total_workouts=total_workouts,
                daily_summary=daily_summary
            )

        except Exception as e:
            logger.error(f"운동 정보 저장 실패: {e}")
            await db.rollback()
            raise ServerException(f"운동 정보 저장 실패: {str(e)}")

    async def get_user_workouts(self, user_id: int, year: int = None, month: int = None, db: AsyncSession = None) -> List[WorkoutInfo]:
        """
        사용자의 운동 정보 조회

        Args:
            user_id: 사용자 ID
            year: 년도 (선택사항)
            month: 월 (선택사항)
            db: 데이터베이스 세션

        Returns:
            운동 정보 목록

        Raises:
            NotFoundException: 사용자를 찾을 수 없음
        """
        try:
            query = select(Workout).where(Workout.user_id == user_id)
            
            if year is not None:
                query = query.where(Workout.year == year)
            if month is not None:
                query = query.where(Workout.month == month)
            
            query = query.order_by(Workout.year.desc(), Workout.month.desc(), Workout.created_at.desc())
            
            result = await db.execute(query)
            workouts = result.scalars().all()

            return [
                WorkoutInfo(
                    id=workout.id,
                    user_id=workout.user_id,
                    workout_name=workout.workout_name,
                    year=workout.year,
                    month=workout.month,
                    day=workout.day,
                    created_at=format_datetime(workout.created_at),
                    updated_at=format_datetime(workout.updated_at)
                )
                for workout in workouts
            ]

        except Exception as e:
            logger.error(f"운동 정보 조회 실패: {e}")
            raise ServerException(f"운동 정보 조회 실패: {str(e)}")

    async def _delete_existing_workouts(self, user_id: int, year: int, month: int, db: AsyncSession) -> None:
        """해당 user_id와 연월의 기존 운동 데이터 모두 삭제"""
        delete_stmt = delete(Workout).where(
            Workout.user_id == user_id,
            Workout.year == year,
            Workout.month == month
        )
        await db.execute(delete_stmt)
