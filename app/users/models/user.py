from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.base.base_time_entity import BaseTimeEntity


class User(BaseTimeEntity):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)

    # 인덱스 생성
    __table_args__ = (
        Index('idx_username', 'username'),
    )

    # 운동 정보와의 관계
    workouts = relationship("Workout", back_populates="user")

    # 식단 정보와의 관계
    diets = relationship("Diet", back_populates="user")

