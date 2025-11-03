"""
운동 정보 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.base.base_time_entity import BaseTimeEntity


class Workout(BaseTimeEntity):
    __tablename__ = 'workouts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    workout_name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    
    # 사용자와의 관계
    user = relationship("User", back_populates="workouts")
