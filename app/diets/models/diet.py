"""
식단 정보 모델
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.base.base_time_entity import BaseTimeEntity


class Diet(BaseTimeEntity):
    __tablename__ = 'diets'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    food_name = Column(String(100), nullable=False)
    calories = Column(Float, nullable=False)
    meal_type = Column(String(20), nullable=False)  # breakfast, lunch, dinner, snack
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    
    # 사용자와의 관계
    user = relationship("User", back_populates="diets")
