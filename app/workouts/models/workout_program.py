"""
운동 프로그램 정보 모델 (CSV 데이터)
"""
from sqlalchemy import Column, Integer, String, Index
from app.base.base_time_entity import BaseTimeEntity


class WorkoutProgram(BaseTimeEntity):
    __tablename__ = 'workout_programs'

    id = Column(Integer, primary_key=True, index=True)
    program_number = Column(Integer, nullable=False, unique=True, index=True)  # CSV의 번호
    category_large = Column(String(100), nullable=False)  # 대분류
    category_medium = Column(String(100), nullable=False)  # 중분류
    category_small = Column(String(100), nullable=False)  # 소분류
    title = Column(String(500), nullable=False)  # 제목
    video_url = Column(String(500), nullable=False)  # 동영상주소

    # 인덱스 생성
    __table_args__ = (
        Index('idx_program_number', 'program_number'),
        Index('idx_category_large', 'category_large'),
        Index('idx_category_medium', 'category_medium'),
    )
