"""
처방 추천 모델 학습 스크립트 (멀티라벨 운동 태그 추천, 상위 3개 반환)
DB에서 데이터를 가져와 pres_note로부터 운동 태그를 만들고,
키·몸무게·BMI 특징으로 태그 확률을 예측해 상위 3개 운동을 추천
"""

import re
import json
import joblib
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import Counter
import asyncio

from sqlalchemy import select

from sklearn.model_selection import KFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import f1_score

from app.workouts.models.physical_fitness_result import PhysicalFitnessResult
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# =========================
# 설정
# =========================
MIN_HEIGHT, MAX_HEIGHT = 120, 220
MIN_WEIGHT, MAX_WEIGHT = 30, 250
MIN_BMI, MAX_BMI = 10, 60

N_SPLITS = 5
RANDOM_STATE = 42
TOP_K = 3  # 추천 개수

# pres_note에서 운동 태그를 뽑는 키워드 사전
# 필요 시 자유롭게 보강
KEYWORDS: Dict[str, List[str]] = {
    # 유산소
    "walking": ["걷기", "만보", "빠르게 걷기", "속보", "파워워킹"],
    "jogging": ["조깅", "러닝", "런닝", "러닝머신", "트레드밀", "가볍게 뛰기"],
    "cycling": ["사이클", "자전거", "실내자전거", "스피닝"],
    "swimming": ["수영", "자유형", "평영", "배영"],
    "aerobic_interval": ["인터벌", "고강도", "interval", "HIIT", "스프린트"],

    # 근력
    "strength_lower": ["스쿼트", "런지", "레그프레스", "레그컬", "힙쓰러스트", "데드리프트", "하체 근력"],
    "strength_upper": ["푸시업", "벤치프레스", "랫풀다운", "풀업", "덤벨프레스", "숄더프레스", "상체 근력"],
    "strength_core": ["플랭크", "데드버그", "버드독", "크런치", "복근", "코어"],

    # 유연성/균형
    "flexibility": ["스트레칭", "유연성", "햄스트링 스트레칭", "전굴", "하체 스트레칭", "상체 스트레칭"],
    "balance": ["균형", "밸런스", "스텝", "자세 안정", "싱글 레그 스탠스"],
}

# 학습 대상 태그 목록
TAGS: List[str] = list(KEYWORDS.keys())

# =========================
# 유틸
# =========================
def normalize_text(s: str) -> str:
    s = str(s).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def compute_bmi(height_cm: float, weight_kg: float) -> float:
    h_m = height_cm / 100.0
    if h_m <= 0:
        return np.nan
    return weight_kg / (h_m ** 2)

def extract_tags(note_norm: str) -> List[str]:
    """정규화된 pres_note에서 운동 태그 추출"""
    found = []
    for tag, kws in KEYWORDS.items():
        for kw in kws:
            if kw in note_norm:
                found.append(tag)
                break
    return list(set(found))

def to_multihot(tag_list: List[str], all_tags: List[str]) -> np.ndarray:
    v = np.zeros(len(all_tags), dtype=int)
    for t in tag_list:
        if t in all_tags:
            v[all_tags.index(t)] = 1
    return v

async def load_data_from_db() -> pd.DataFrame:
    """DB에서 학습 데이터 로드"""
    async with AsyncSessionLocal() as db:
        try:
            query = select(PhysicalFitnessResult).where(
                PhysicalFitnessResult.height_cm.isnot(None),
                PhysicalFitnessResult.weight_kg.isnot(None),
                PhysicalFitnessResult.pres_note.isnot(None),
                PhysicalFitnessResult.height_cm != '',
                PhysicalFitnessResult.weight_kg != '',
                PhysicalFitnessResult.pres_note != ''
            )
            result = await db.execute(query)
            records = result.scalars().all()

            data = []
            for record in records:
                try:
                    height = float(record.height_cm) if str(record.height_cm).strip() else None
                    weight = float(record.weight_kg) if str(record.weight_kg).strip() else None
                    pres_note = record.pres_note.strip() if str(record.pres_note).strip() else None
                    if height and weight and pres_note:
                        data.append({"height_cm": height, "weight_kg": weight, "pres_note": pres_note})
                except Exception as e:
                    logger.debug(f"데이터 변환 실패(id={getattr(record,'id',None)}): {e}")
                    continue

            df = pd.DataFrame(data)
            logger.info(f"DB 로드 완료: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"DB 데이터 로드 실패: {e}")
            raise

# =========================
# 학습 메인
# =========================
async def train_model():
    logger.info("=" * 80)
    logger.info("처방 추천 모델 학습 시작")
    logger.info("=" * 80)

    # 1) 데이터 로딩
    df = await load_data_from_db()
    if len(df) == 0:
        logger.warning("학습 데이터가 없습니다.")
        return

    # 2) 전처리 및 파생
    df["pres_note_norm"] = df["pres_note"].apply(normalize_text)
    df["bmi"] = df.apply(lambda r: compute_bmi(r["height_cm"], r["weight_kg"]), axis=1)

    # 3) 이상치 제거
    mask = (
        df["height_cm"].between(MIN_HEIGHT, MAX_HEIGHT, inclusive="both") &
        df["weight_kg"].between(MIN_WEIGHT, MAX_WEIGHT, inclusive="both") &
        df["bmi"].between(MIN_BMI, MAX_BMI, inclusive="both")
    )
    df = df[mask].reset_index(drop=True)
    if len(df) == 0:
        logger.warning("이상치 제거 후 데이터가 없습니다.")
        return
    logger.info(f"정상 범위 데이터: {len(df)}")

    # 4) pres_note에서 운동 태그 추출
    df["tags"] = df["pres_note_norm"].apply(extract_tags)
    df = df[df["tags"].map(len) > 0].reset_index(drop=True)  # 태그 없는 레코드 제거
    if len(df) == 0:
        logger.warning("운동 태그가 추출된 레코드가 없습니다. KEYWORDS 사전을 점검하세요.")
        return

    # 멀티핫 라벨 행렬
    Y = np.stack(df["tags"].apply(lambda tags: to_multihot(tags, TAGS)).values)  # shape: (n, K)

    # 5) 특징 정의
    bmi_bins = [0, 16, 18.5, 23, 25, 30, 35, 100]
    df["bmi_bucket"] = pd.cut(df["bmi"], bins=bmi_bins, labels=False, include_lowest=True)
    df = df.dropna(subset=["bmi_bucket"]).reset_index(drop=True)
    Y = Y[: len(df)]

    num_features = ["height_cm", "weight_kg", "bmi"]
    cat_features = ["bmi_bucket"]

    preprocess = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", dtype=np.float64), cat_features),
        ]
    )

    # 6) 모델 구성
    base_lr = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        solver="lbfgs"  # predict_proba 사용
    )
    ovr_lr = OneVsRestClassifier(base_lr)

    # 파이프라인 없이 전처리 결과를 공유해 OVR와 KNN 모두 동일 입력을 쓰도록 함
    X = df[num_features + cat_features]
    X_mat = preprocess.fit_transform(X)

    # 로지스틱 OVR 학습
    ovr_lr.fit(X_mat, Y)

    # KNN은 multilabel이므로 확률 대신 이웃들의 라벨 평균을 점수로 사용
    knn = KNeighborsClassifier(n_neighbors=7, weights="distance")
    knn.fit(X_mat, Y)

    # 7) 교차검증
    # 멀티라벨은 StratifiedKFold가 불가하므로 KFold 사용
    kf = KFold(n_splits=min(N_SPLITS, max(2, len(df)//50)), shuffle=True, random_state=RANDOM_STATE)
    micro_f1s, macro_f1s = [], []

    for fold, (tr, va) in enumerate(kf.split(X_mat), 1):
        X_tr, X_va = X_mat[tr], X_mat[va]
        Y_tr, Y_va = Y[tr], Y[va]

        ovr_lr_fold = OneVsRestClassifier(
            LogisticRegression(class_weight="balanced", max_iter=1000, solver="lbfgs")
        ).fit(X_tr, Y_tr)

        # 로지스틱 확률
        proba_lr = np.clip(ovr_lr_fold.predict_proba(X_va), 1e-9, 1 - 1e-9)

        # KNN 이웃 라벨 평균 점수
        knn_fold = KNeighborsClassifier(n_neighbors=7, weights="distance").fit(X_tr, Y_tr)
        neigh_dist, neigh_idx = knn_fold.kneighbors(X_va, n_neighbors=7, return_distance=True)
        # 거리 가중 평균
        w = 1 / (neigh_dist + 1e-6)
        w = w / w.sum(axis=1, keepdims=True)
        score_knn = np.einsum("ij,ijk->ik", w, Y_tr[neigh_idx])

        # 결합 점수
        score = 0.7 * proba_lr + 0.3 * score_knn

        # 임계치 0.5로 이진화
        Y_pred = (score >= 0.5).astype(int)
        # 빈 예측 방지: 모두 0이면 상위 1개는 1로
        zeros = Y_pred.sum(axis=1) == 0
        if np.any(zeros):
            top1 = np.argmax(score[zeros], axis=1)
            Y_pred[zeros, top1] = 1

        micro_f1s.append(f1_score(Y_va, Y_pred, average="micro", zero_division=0))
        macro_f1s.append(f1_score(Y_va, Y_pred, average="macro", zero_division=0))

    cv_results = {
        "cv_micro_f1": float(np.mean(micro_f1s)) if micro_f1s else None,
        "cv_macro_f1": float(np.mean(macro_f1s)) if macro_f1s else None
    }
    logger.info(f"교차검증 결과: {cv_results}")

    # 8) 최종 저장
    model_dir = Path(__file__).parent.parent.parent.parent / "models"
    model_dir.mkdir(exist_ok=True)

    preprocess_path = model_dir / "prescriptor_preprocess.joblib"
    ovr_path = model_dir / "prescriptor_ovr_lr.joblib"
    knn_path = model_dir / "prescriptor_knn.joblib"
    meta_path = model_dir / "prescriptor_meta.json"

    joblib.dump(preprocess, preprocess_path)
    joblib.dump(ovr_lr, ovr_path)
    joblib.dump(knn, knn_path)

    meta = {
        "version": "ml-tags-1.0.0",
        "tags": TAGS,
        "num_features": num_features,
        "cat_features": cat_features,
        "bmi_bins": bmi_bins,
        "cv_results": cv_results,
        "n_samples": int(len(df))
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info("=" * 80)
    logger.info("모델 학습 완료")
    logger.info(f"전처리 저장: {preprocess_path}")
    logger.info(f"OVR 로지스틱 저장: {ovr_path}")
    logger.info(f"KNN 저장: {knn_path}")
    logger.info(f"메타 저장: {meta_path}")
    logger.info("=" * 80)

# =========================
# 예측 헬퍼: 키·몸무게 입력 → 상위 3개 태그 추천
# =========================
def recommend_top3(height_cm: float, weight_kg: float, model_dir: Path) -> Dict[str, Any]:
    preprocess = joblib.load(model_dir / "prescriptor_preprocess.joblib")
    ovr_lr = joblib.load(model_dir / "prescriptor_ovr_lr.joblib")
    knn = joblib.load(model_dir / "prescriptor_knn.joblib")

    with open(model_dir / "prescriptor_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    tags = meta["tags"]
    bmi_bins = meta["bmi_bins"]
    num_features = meta["num_features"]
    cat_features = meta["cat_features"]

    bmi = compute_bmi(height_cm, weight_kg)
    # bmi_bucket 계산
    # np.digitize는 내부 경계 사용, bins는 [0,16,18.5,23,25,30,35,100]
    bucket = int(np.digitize([bmi], bins=bmi_bins[1:-1], right=False)[0])

    X_in = pd.DataFrame([{
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
        "bmi_bucket": bucket
    }], columns=num_features + cat_features)

    X_mat = preprocess.transform(X_in)

    proba_lr = np.clip(ovr_lr.predict_proba(X_mat), 1e-9, 1 - 1e-9)[0]

    # KNN 이웃 라벨 평균
    neigh_dist, neigh_idx = knn.kneighbors(X_mat, n_neighbors=7, return_distance=True)
    w = 1 / (neigh_dist + 1e-6)
    w = w / w.sum(axis=1, keepdims=True)
    score_knn = (w @ knn._y)[0] if hasattr(knn, "_y") else np.mean(knn.predict(X_mat), axis=0)

    score = 0.7 * proba_lr + 0.3 * score_knn
    order = np.argsort(score)[::-1][:TOP_K]
    recs = [{"tag": tags[i], "score": float(score[i])} for i in order]

    return {
        "bmi": float(bmi),
        "recommendations": recs  # 상위 3개
    }

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    asyncio.run(train_model())
