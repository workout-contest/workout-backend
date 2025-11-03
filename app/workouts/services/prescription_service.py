"""
처방 추천 서비스 (AI 모델 기반)
"""
import logging
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PrescriptionService:
    """처방 추천 서비스 클래스"""
    
    def __init__(self):
        self.preprocess = None
        self.ovr_lr = None
        self.knn = None
        self.meta = None
        self.model_loaded = False
        self._load_model()
    
    def _load_model(self):
        """모델 및 메타데이터 로드"""
        try:
            model_dir = Path(__file__).parent.parent.parent.parent / "models"
            preprocess_path = model_dir / "prescriptor_preprocess.joblib"
            ovr_path = model_dir / "prescriptor_ovr_lr.joblib"
            knn_path = model_dir / "prescriptor_knn.joblib"
            meta_path = model_dir / "prescriptor_meta.json"
            
            if not preprocess_path.exists() or not ovr_path.exists() or not knn_path.exists() or not meta_path.exists():
                logger.warning("모델 파일이 없습니다. 먼저 모델을 학습해야 합니다.")
                return
            
            self.preprocess = joblib.load(preprocess_path)
            self.ovr_lr = joblib.load(ovr_path)
            self.knn = joblib.load(knn_path)
            
            with open(meta_path, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
            
            self.model_loaded = True
            logger.info("처방 추천 모델 로드 완료")
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            self.model_loaded = False
    
    def predict_prescription(
        self, 
        height_cm: float, 
        weight_kg: float, 
        top_k: int = 3,
        conf_thr: float = 0.55
    ) -> Dict[str, Any]:
        """
        처방 추천 예측
        
        Args:
            height_cm: 키 (cm)
            weight_kg: 몸무게 (kg)
            top_k: 상위 추천 개수
            conf_thr: 신뢰도 임계치
            
        Returns:
            처방 추천 결과
        """
        # 모델이 로드되지 않았으면 다시 로드 시도
        if not self.model_loaded:
            logger.info("모델이 로드되지 않았습니다. 모델을 다시 로드 시도 중...")
            self._load_model()
            if not self.model_loaded:
                raise ValueError("모델이 로드되지 않았습니다. 먼저 모델을 학습해야 합니다.")
        
        try:
            # BMI 계산
            bmi = weight_kg / ((height_cm / 100.0) ** 2)
            
            # BMI 버킷 계산
            bmi_bins = self.meta["bmi_bins"]
            bmi_bucket = pd.cut([bmi], bins=bmi_bins, labels=False, include_lowest=True)[0]
            
            # 입력 데이터 생성
            num_features = self.meta["num_features"]
            cat_features = self.meta["cat_features"]
            X = pd.DataFrame([{
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "bmi": bmi,
                "bmi_bucket": bmi_bucket
            }])
            
            # 전처리
            X_mat = self.preprocess.transform(X)
            
            # 예측
            tags = self.meta["tags"]
            
            # 로지스틱 확률
            proba_lr = np.clip(self.ovr_lr.predict_proba(X_mat)[0], 1e-9, 1 - 1e-9)
            
            # KNN 이웃 라벨 평균 점수
            neigh_dist, neigh_idx = self.knn.kneighbors(X_mat, n_neighbors=7, return_distance=True)
            w = 1 / (neigh_dist[0] + 1e-6)
            w = w / w.sum()
            # 학습 데이터가 필요하지만 저장되지 않았으므로, 간단히 로지스틱만 사용
            # score_knn = np.einsum("j,jk->k", w, Y_train[neigh_idx[0]])
            # score = 0.7 * proba_lr + 0.3 * score_knn
            score = proba_lr  # 로지스틱만 사용
            
            # 상위 top_k 선택
            order = np.argsort(score)[::-1][:top_k]
            
            # 영어 태그를 한국어로 변환
            tag_to_korean = {
                "walking": "걷기",
                "jogging": "조깅",
                "cycling": "자전거",
                "swimming": "수영",
                "aerobic_interval": "고강도 인터벌",
                "strength_lower": "하체 근력 운동",
                "strength_upper": "상체 근력 운동",
                "strength_core": "코어 운동",
                "flexibility": "스트레칭",
                "balance": "균형 운동"
            }
            
            candidates = [
                {
                    "pres_note": tag_to_korean.get(tags[i], tags[i]), 
                    "prob": float(score[i])
                } 
                for i in order
            ]
            
            return candidates
            
        except Exception as e:
            logger.error(f"처방 예측 실패: {e}")
            raise ValueError(f"처방 예측 실패: {str(e)}")
    


# 싱글톤 인스턴스
_prescription_service = None


def get_prescription_service() -> PrescriptionService:
    """처방 추천 서비스 싱글톤 인스턴스 반환"""
    global _prescription_service
    if _prescription_service is None:
        _prescription_service = PrescriptionService()
    return _prescription_service


def reload_prescription_service():
    """처방 추천 서비스 싱글톤 인스턴스 재로드 (모델 학습 후 호출)"""
    global _prescription_service
    _prescription_service = PrescriptionService()
    return _prescription_service

