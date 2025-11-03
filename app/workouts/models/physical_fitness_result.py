"""
체력 측정 결과 모델
"""
from sqlalchemy import Column, Integer, String, Index, Text
from app.base.base_time_entity import BaseTimeEntity


class PhysicalFitnessResult(BaseTimeEntity):
    __tablename__ = 'physical_fitness_results'

    id = Column(Integer, primary_key=True, index=True)
    row_num = Column(String(50), nullable=True)  # 순번
    age_class = Column(String(50), nullable=True, index=True)  # 측정자연령대
    age_degree = Column(String(50), nullable=True)  # 측정자나이
    age_gbn = Column(String(50), nullable=True, index=True)  # 측정자연령구분
    cert_gbn = Column(String(50), nullable=True, index=True)  # 상장구분
    test_ym = Column(String(20), nullable=True, index=True)  # 측정연월
    test_sex = Column(String(10), nullable=True, index=True)  # 측정자성별
    
    # 기본 체력 측정 항목
    height_cm = Column(String(100), nullable=True)  # 신장(cm) - item_f001
    weight_kg = Column(String(100), nullable=True)  # 체중(kg) - item_f002
    body_fat_percent = Column(String(100), nullable=True)  # 체지방율(%) - item_f003
    waist_circumference_cm = Column(String(100), nullable=True)  # 허리둘레(cm) - item_f004
    
    # 혈압
    diastolic_bp_mmhg = Column(String(100), nullable=True)  # 이완기혈압_최저(mmHg) - item_f005
    systolic_bp_mmhg = Column(String(100), nullable=True)  # 수축기혈압_최고(mmHg) - item_f006
    
    # 악력
    grip_strength_left_kg = Column(String(100), nullable=True)  # 악력_좌(kg) - item_f007
    grip_strength_right_kg = Column(String(100), nullable=True)  # 악력_우(kg) - item_f008
    
    # 유연성 및 근력
    sit_up_count = Column(String(100), nullable=True)  # 윗몸말아올리기(회) - item_f009
    repeated_jump_count = Column(String(100), nullable=True)  # 반복점프(회) - item_f010
    sit_reach_cm = Column(String(100), nullable=True)  # 앉아윗몸말아올리기(cm) - item_f012
    sit_up_cross_count = Column(String(100), nullable=True)  # 교차윗몸일으키기(회) - item_f019
    
    # 민첩성 및 순발력
    illinois_seconds = Column(String(100), nullable=True)  # 일리노이(초) - item_f013
    hang_time_seconds = Column(String(100), nullable=True)  # 체공시간(초) - item_f014
    adult_hang_time_seconds = Column(String(100), nullable=True)  # 성인체공시간(초) - item_f041
    standing_long_jump_cm = Column(String(100), nullable=True)  # 제자리 멀리뛰기(cm) - item_f022
    repeated_side_jump_count = Column(String(100), nullable=True)  # 반복옆뛰기(회) - item_f043
    
    # 협응력
    coordination_time_seconds = Column(String(100), nullable=True)  # 협응력시간(초) - item_f015
    coordination_error_count = Column(String(100), nullable=True)  # 협응력실수횟수(회) - item_f016
    coordination_result_seconds = Column(String(100), nullable=True)  # 협응력계산결과값(초) - item_f017
    hand_eye_coordination_count = Column(String(100), nullable=True)  # 눈-손 협응력(벽패스)(회) - item_f044
    
    # 심폐지구력
    shuttle_run_count = Column(String(100), nullable=True)  # 왕복오래달리기(회) - item_f020
    shuttle_run_vo2max = Column(String(100), nullable=True)  # 왕복오래달리기_출력(VO₂max) - item_f030
    run_10m_4times_seconds = Column(String(100), nullable=True)  # 10M 4회 왕복달리기(초) - item_f021
    run_5m_4times_seconds = Column(String(100), nullable=True)  # 5m 4회 왕복달리기(초) - item_f050
    six_minute_walk_m = Column(String(100), nullable=True)  # 6분걷기(m) - item_f024
    two_minute_walk_in_place_count = Column(String(100), nullable=True)  # 2분제자리걷기(회) - item_f025
    
    # 트레드밀
    treadmill_rest_bpm = Column(String(100), nullable=True)  # 트레드밀_안정시(bpm) - item_f031
    treadmill_3min_bpm = Column(String(100), nullable=True)  # 트레드밀_3분(bpm) - item_f032
    treadmill_6min_bpm = Column(String(100), nullable=True)  # 트레드밀_6분(bpm) - item_f033
    treadmill_9min_bpm = Column(String(100), nullable=True)  # 트레드밀_9분(bpm) - item_f034
    treadmill_vo2max = Column(String(100), nullable=True)  # 트레드밀_출력(VO₂max) - item_f035
    
    # 스텝검사
    step_test_recovery_bpm = Column(String(100), nullable=True)  # 스텝검사_회복시 심박수(bpm) - item_f036
    step_test_vo2max = Column(String(100), nullable=True)  # 스텝검사_출력(VO₂max) - item_f037
    
    # 기타 체력 항목
    chair_stand_count = Column(String(100), nullable=True)  # 의자에앉았다일어서기(회) - item_f023
    chair_sit_3m_return_count = Column(String(100), nullable=True)  # 의자에앉아 3M표적 돌아오기(회) - item_f026
    figure_8_walk_count = Column(String(100), nullable=True)  # 8자보행(회) - item_f027
    reaction_time_seconds = Column(String(100), nullable=True)  # 반응시간(초) - item_f040
    button_3x3_seconds = Column(String(100), nullable=True)  # 3×3 버튼누르기(초) - item_f051
    
    # 지수 및 계산값
    bmi = Column(String(100), nullable=True)  # BMI(kg/㎡) - item_f018
    relative_grip_strength_percent = Column(String(100), nullable=True)  # 상대악력(%) - item_f028
    absolute_grip_strength_kg = Column(String(100), nullable=True)  # 절대악력(kg) - item_f052
    waist_height_ratio = Column(String(100), nullable=True)  # 허리둘레-신장비(WHtR) - item_f042
    
    # 신체 사이즈
    thigh_left_cm = Column(String(100), nullable=True)  # 허벅지_좌(cm) - item_f038
    thigh_right_cm = Column(String(100), nullable=True)  # 허벅지_우(cm) - item_f039
    
    # 운동처방
    pres_note = Column(Text, nullable=True)  # 운동처방내용

    # 인덱스 생성
    __table_args__ = (
        Index('idx_test_ym_sex', 'test_ym', 'test_sex'),
        Index('idx_age_class_gbn', 'age_class', 'age_gbn'),
    )
