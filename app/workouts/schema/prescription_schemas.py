"""
처방 추천 관련 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class PrescriptionCandidate(BaseModel):
    """처방 후보"""
    pres_note: str = Field(..., description="처방 내용")
    prob: float = Field(..., ge=0.0, le=1.0, description="확률")


class PrescriptionRequest(BaseModel):
    """처방 추천 요청"""
    height_cm: float = Field(..., gt=0, description="키 (cm)")
    weight_kg: float = Field(..., gt=0, description="몸무게 (kg)")
    top_k: Optional[int] = Field(3, ge=1, le=10, description="상위 추천 개수")
    conf_thr: Optional[float] = Field(0.55, ge=0.0, le=1.0, description="신뢰도 임계치")


class PrescriptionResponse(BaseModel):
    """처방 추천 응답"""
    pass  # 실제로는 List[PrescriptionCandidate]를 반환하지만 스키마는 유지

