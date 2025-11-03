"""
식단 서비스
"""
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.diets.models.diet import Diet
from app.diets.schema.schemas import MonthlyDietRequest, DietResponse, DietInfo, MealInfo
from app.core.exceptions import ServerException
from app.core.utils import format_datetime

logger = logging.getLogger(__name__)


class DietService:
    """식단 서비스 클래스"""

    async def save_diet(self, user_id: int, diet_data: MonthlyDietRequest, db: AsyncSession) -> DietResponse:
        """
        월별 식단 정보 저장 (기존 데이터 삭제 후 새로 저장)

        Args:
            user_id: 사용자 ID
            diet_data: 월별 식단 정보 요청 데이터
            db: 데이터베이스 세션

        Returns:
            식단 정보 저장 응답

        Raises:
            ServerException: 서버 오류
        """
        try:
            # 해당 user_id와 연월의 기존 데이터 모두 삭제
            await self._delete_existing_diets(user_id, diet_data.year, diet_data.month, db)
            
            daily_summary = {}
            total_meals = 0
            
            # 각 일별로 식단 저장
            for daily_diet in diet_data.daily_diets:
                saved_meals = []
                
                # 해당 일의 각 식사 저장
                for meal in daily_diet.meals:
                    # 새 식단 정보 생성
                    new_diet = Diet(
                        user_id=user_id,
                        food_name=meal.food_name,
                        calories=meal.calories,
                        meal_type=meal.meal_type,
                        year=diet_data.year,
                        month=diet_data.month,
                        day=daily_diet.day
                    )
                    
                    db.add(new_diet)
                    saved_meals.append(meal)
                    total_meals += 1
                
                daily_summary[daily_diet.day] = saved_meals
            
            await db.commit()

            return DietResponse(
                message=f"{len(diet_data.daily_diets)}일, 총 {total_meals}개의 식단 정보가 저장되었습니다.",
                user_id=user_id,
                year=diet_data.year,
                month=diet_data.month,
                saved_days=len(diet_data.daily_diets),
                total_meals=total_meals,
                daily_summary=daily_summary
            )

        except Exception as e:
            logger.error(f"식단 정보 저장 실패: {e}")
            await db.rollback()
            raise ServerException(f"식단 정보 저장 실패: {str(e)}")

    async def get_user_diets(self, user_id: int, year: int = None, month: int = None, db: AsyncSession = None) -> List[DietInfo]:
        """
        사용자의 식단 정보 조회

        Args:
            user_id: 사용자 ID
            year: 년도 (선택사항)
            month: 월 (선택사항)
            db: 데이터베이스 세션

        Returns:
            식단 정보 목록

        Raises:
            ServerException: 서버 오류
        """
        try:
            query = select(Diet).where(Diet.user_id == user_id)
            
            if year is not None:
                query = query.where(Diet.year == year)
            if month is not None:
                query = query.where(Diet.month == month)
            
            query = query.order_by(Diet.year.desc(), Diet.month.desc(), Diet.created_at.desc())
            
            result = await db.execute(query)
            diets = result.scalars().all()

            return [
                DietInfo(
                    id=diet.id,
                    user_id=diet.user_id,
                    food_name=diet.food_name,
                    calories=diet.calories,
                    meal_type=diet.meal_type,
                    year=diet.year,
                    month=diet.month,
                    day=diet.day,
                    created_at=format_datetime(diet.created_at),
                    updated_at=format_datetime(diet.updated_at)
                )
                for diet in diets
            ]

        except Exception as e:
            logger.error(f"식단 정보 조회 실패: {e}")
            raise ServerException(f"식단 정보 조회 실패: {str(e)}")

    async def _delete_existing_diets(self, user_id: int, year: int, month: int, db: AsyncSession) -> None:
        """해당 user_id와 연월의 기존 식단 데이터 모두 삭제"""
        delete_stmt = delete(Diet).where(
            Diet.user_id == user_id,
            Diet.year == year,
            Diet.month == month
        )
        await db.execute(delete_stmt)
