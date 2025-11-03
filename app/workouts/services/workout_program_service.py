"""
운동 프로그램 서비스 (CSV 데이터 로딩)
"""
import csv
import logging
from pathlib import Path
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.workouts.models.workout_program import WorkoutProgram
from app.workouts.schema.schemas import WorkoutProgramInfo
from app.core.database import AsyncSessionLocal
from app.core.utils import format_datetime

logger = logging.getLogger(__name__)


class WorkoutProgramService:
    """운동 프로그램 서비스 클래스"""

    async def load_csv_to_db(self) -> tuple[int, int]:
        """
        CSV 파일을 읽어서 DB에 저장 (이미 있으면 스킵)

        Returns:
            (저장된 개수, 스킵된 개수) 튜플
        """
        csv_file_path = Path(__file__).parent.parent.parent.parent / "서울올림픽기념국민체육진흥공단_국민체력100 운동처방 동영상주소 정보_20210727.csv"
        
        if not csv_file_path.exists():
            logger.warning(f"CSV 파일을 찾을 수 없습니다: {csv_file_path}")
            return 0, 0

        saved_count = 0
        skipped_count = 0

        async with AsyncSessionLocal() as db:
            try:
                # CSV 파일 읽기 (CP949 인코딩)
                with open(csv_file_path, 'r', encoding='cp949') as f:
                    reader = csv.reader(f)
                    headers = next(reader)  # 헤더 스킵

                    for row in reader:
                        if len(row) < 6:
                            continue
                        
                        try:
                            program_number = int(row[0])
                            category_large = row[1].strip()
                            category_medium = row[2].strip()
                            category_small = row[3].strip()
                            title = row[4].strip()
                            video_url = row[5].strip()
                        except (ValueError, IndexError) as e:
                            logger.warning(f"CSV 행 파싱 실패: {row}, 오류: {e}")
                            continue

                        # 이미 존재하는지 확인
                        existing = await db.execute(
                            select(WorkoutProgram).where(
                                WorkoutProgram.program_number == program_number
                            )
                        )
                        if existing.scalar_one_or_none() is not None:
                            skipped_count += 1
                            continue

                        # 새 프로그램 생성
                        program = WorkoutProgram(
                            program_number=program_number,
                            category_large=category_large,
                            category_medium=category_medium,
                            category_small=category_small,
                            title=title,
                            video_url=video_url
                        )
                        db.add(program)
                        saved_count += 1

                    await db.commit()
                    logger.info(f"CSV 데이터 로딩 완료: {saved_count}개 저장, {skipped_count}개 스킵")

            except Exception as e:
                logger.error(f"CSV 데이터 로딩 실패: {e}")
                await db.rollback()
                raise

        return saved_count, skipped_count


    async def get_programs_by_category_small(self, category_small: str, db: AsyncSession) -> List[WorkoutProgramInfo]:
        """
        소분류로 운동 프로그램 조회

        Args:
            category_small: 소분류
            db: 데이터베이스 세션

        Returns:
            운동 프로그램 정보 목록
        """
        try:
            query = select(WorkoutProgram).where(
                WorkoutProgram.category_small == category_small
            ).order_by(WorkoutProgram.program_number.asc())

            result = await db.execute(query)
            programs = result.scalars().all()

            return [
                WorkoutProgramInfo(
                    id=program.id,
                    program_number=program.program_number,
                    category_large=program.category_large,
                    category_medium=program.category_medium,
                    category_small=program.category_small,
                    title=program.title,
                    video_url=program.video_url,
                    created_at=format_datetime(program.created_at),
                    updated_at=format_datetime(program.updated_at)
                )
                for program in programs
            ]

        except Exception as e:
            logger.error(f"운동 프로그램 조회 실패: {e}")
            raise


async def load_workout_programs_from_csv():
    """CSV에서 운동 프로그램 데이터를 로드하는 편의 함수"""
    service = WorkoutProgramService()
    return await service.load_csv_to_db()
