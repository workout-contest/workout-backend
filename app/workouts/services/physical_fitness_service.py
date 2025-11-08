"""
체력 측정 결과 서비스 (공공데이터 API 연동)
"""
import logging
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
import aiohttp
import asyncio
from urllib.parse import urlencode

from app.workouts.models.physical_fitness_result import PhysicalFitnessResult
from app.core.database import AsyncSessionLocal
from config import settings

logger = logging.getLogger(__name__)


class PhysicalFitnessService:
    """체력 측정 결과 서비스 클래스"""

    async def fetch_data_from_api(
        self,
        page_no: int = 1,
        num_of_rows: int = 100,
        age_class: Optional[str] = None,
        age_gbn: Optional[str] = None,
        cert_gbn: Optional[str] = None,
        start_test_ym: Optional[str] = None,
        end_test_ym: Optional[str] = None,
        test_sex: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        공공데이터 API에서 체력 측정 결과 데이터 조회

        Args:
            page_no: 페이지 번호
            num_of_rows: 한 페이지 결과 수
            age_class: 측정자연령대
            age_gbn: 측정자연령구분
            cert_gbn: 상장구분
            start_test_ym: 시작측정년월
            end_test_ym: 종료측정년월
            test_sex: 측정자성별

        Returns:
            API 응답 데이터
        """
        base_url = settings.public_data_api_base_url
        service_key = settings.public_data_api_key
        
        # 공공데이터 API는 인코딩된 키를 그대로 사용해야 함
        # urlencode를 사용하면 이미 인코딩된 키가 다시 인코딩될 수 있으므로
        # serviceKey는 params에 포함하지 않고 URL에 직접 추가
        
        params = {
            'pageNo': str(page_no),
            'numOfRows': str(num_of_rows),
            'resultType': 'JSON'
        }
        
        if age_class:
            params['age_class'] = age_class
        if age_gbn:
            params['age_gbn'] = age_gbn
        if cert_gbn:
            params['cert_gbn'] = cert_gbn
        if start_test_ym:
            params['starttest_ym'] = start_test_ym
        if end_test_ym:
            params['endtest_ym'] = end_test_ym
        if test_sex:
            params['test_sex'] = test_sex

        # serviceKey를 먼저 추가하고 나머지 파라미터는 urlencode로 처리
        # 인코딩된 키는 그대로 사용 (urlencode 하지 않음)
        url = f"{base_url}/TODZ_NFA_TEST_RESULT_NEW?serviceKey={service_key}&{urlencode(params)}"
        
        logger.info(f"[API 호출] 페이지 {page_no} 요청 시작")
        logger.debug(f"API 호출 URL: {url[:200]}...")  # 로깅 (키는 마스킹하지 않음, 디버그용)

        try:
            request_start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    request_time = time.time() - request_start
                    logger.info(f"[API 호출] 페이지 {page_no} 응답 수신 (HTTP {response.status}, 소요: {request_time:.2f}초)")
                    response_text = await response.text()
                    
                    if response.status == 200:
                        # text/json MIME 타입 때문에 직접 파싱 필요
                        import json
                        try:
                            data = json.loads(response_text)
                            return data
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON 파싱 실패: {e}, 응답 텍스트: {response_text[:500]}")
                            raise Exception(f"JSON 파싱 실패: {e}")
                    else:
                        logger.error(f"API 호출 실패: HTTP {response.status}")
                        logger.error(f"응답 헤더: {dict(response.headers)}")
                        logger.error(f"응답 본문: {response_text[:1000]}")
                        raise Exception(f"API 호출 실패: HTTP {response.status}, 응답: {response_text[:200]}")
        except asyncio.TimeoutError:
            logger.error("API 호출 타임아웃")
            raise Exception("API 호출 타임아웃")
        except Exception as e:
            logger.error(f"API 호출 중 오류 발생: {e}")
            raise

    def _parse_api_response(self, data: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int]:
        """
        API 응답 파싱

        Args:
            data: API 응답 데이터

        Returns:
            (데이터 리스트, 전체 개수) 튜플
        """
        try:
            if 'response' not in data:
                logger.warning("API 응답에 'response' 키가 없습니다")
                return [], 0

            body = data['response'].get('body', {})
            
            # 결과 코드 확인
            result_code = data['response'].get('header', {}).get('resultCode', '')
            if result_code != '00' and result_code != '0':
                result_msg = data['response'].get('header', {}).get('resultMsg', '')
                logger.warning(f"API 결과 코드 오류: {result_code}, 메시지: {result_msg}")
                return [], 0

            total_count = int(body.get('totalCount', 0))
            items = body.get('items', {})
            
            if not items or 'item' not in items:
                return [], total_count

            item_list = items['item']
            
            # 단일 아이템인 경우 리스트로 변환
            if isinstance(item_list, dict):
                item_list = [item_list]

            return item_list, total_count
        except Exception as e:
            logger.error(f"API 응답 파싱 실패: {e}")
            return [], 0

    def _convert_item_to_model(self, item: Dict[str, Any]) -> PhysicalFitnessResult:
        """
        API 응답 아이템을 모델 객체로 변환
        
        Args:
            item: API 응답 아이템
            
        Returns:
            PhysicalFitnessResult 모델 객체
        """
        return PhysicalFitnessResult(
            row_num=item.get('row_num'),
            age_class=item.get('age_class'),
            age_degree=item.get('age_degree'),
            age_gbn=item.get('age_gbn'),
            cert_gbn=item.get('cert_gbn'),
            test_ym=item.get('test_ym'),
            test_sex=item.get('test_sex'),
            # 필드명 매핑
            height_cm=item.get('item_f001'),  # 신장(cm)
            weight_kg=item.get('item_f002'),  # 체중(kg)
            body_fat_percent=item.get('item_f003'),  # 체지방율(%)
            waist_circumference_cm=item.get('item_f004'),  # 허리둘레(cm)
            diastolic_bp_mmhg=item.get('item_f005'),  # 이완기혈압_최저(mmHg)
            systolic_bp_mmhg=item.get('item_f006'),  # 수축기혈압_최고(mmHg)
            grip_strength_left_kg=item.get('item_f007'),  # 악력_좌(kg)
            grip_strength_right_kg=item.get('item_f008'),  # 악력_우(kg)
            sit_up_count=item.get('item_f009'),  # 윗몸말아올리기(회)
            repeated_jump_count=item.get('item_f010'),  # 반복점프(회)
            sit_reach_cm=item.get('item_f012'),  # 앉아윗몸말아올리기(cm)
            illinois_seconds=item.get('item_f013'),  # 일리노이(초)
            hang_time_seconds=item.get('item_f014'),  # 체공시간(초)
            coordination_time_seconds=item.get('item_f015'),  # 협응력시간(초)
            coordination_error_count=item.get('item_f016'),  # 협응력실수횟수(회)
            coordination_result_seconds=item.get('item_f017'),  # 협응력계산결과값(초)
            bmi=item.get('item_f018'),  # BMI(kg/㎡)
            sit_up_cross_count=item.get('item_f019'),  # 교차윗몸일으키기(회)
            shuttle_run_count=item.get('item_f020'),  # 왕복오래달리기(회)
            run_10m_4times_seconds=item.get('item_f021'),  # 10M 4회 왕복달리기(초)
            standing_long_jump_cm=item.get('item_f022'),  # 제자리 멀리뛰기(cm)
            chair_stand_count=item.get('item_f023'),  # 의자에앉았다일어서기(회)
            six_minute_walk_m=item.get('item_f024'),  # 6분걷기(m)
            two_minute_walk_in_place_count=item.get('item_f025'),  # 2분제자리걷기(회)
            chair_sit_3m_return_count=item.get('item_f026'),  # 의자에앉아 3M표적 돌아오기(회)
            figure_8_walk_count=item.get('item_f027'),  # 8자보행(회)
            relative_grip_strength_percent=item.get('item_f028'),  # 상대악력(%)
            shuttle_run_vo2max=item.get('item_f030'),  # 왕복오래달리기_출력(VO₂max)
            treadmill_rest_bpm=item.get('item_f031'),  # 트레드밀_안정시(bpm)
            treadmill_3min_bpm=item.get('item_f032'),  # 트레드밀_3분(bpm)
            treadmill_6min_bpm=item.get('item_f033'),  # 트레드밀_6분(bpm)
            treadmill_9min_bpm=item.get('item_f034'),  # 트레드밀_9분(bpm)
            treadmill_vo2max=item.get('item_f035'),  # 트레드밀_출력(VO₂max)
            step_test_recovery_bpm=item.get('item_f036'),  # 스텝검사_회복시 심박수(bpm)
            step_test_vo2max=item.get('item_f037'),  # 스텝검사_출력(VO₂max)
            thigh_left_cm=item.get('item_f038'),  # 허벅지_좌(cm)
            thigh_right_cm=item.get('item_f039'),  # 허벅지_우(cm)
            reaction_time_seconds=item.get('item_f040'),  # 반응시간(초)
            adult_hang_time_seconds=item.get('item_f041'),  # 성인체공시간(초)
            waist_height_ratio=item.get('item_f042'),  # 허리둘레-신장비(WHtR)
            repeated_side_jump_count=item.get('item_f043'),  # 반복옆뛰기(회)
            hand_eye_coordination_count=item.get('item_f044'),  # 눈-손 협응력(벽패스)(회)
            run_5m_4times_seconds=item.get('item_f050'),  # 5m 4회 왕복달리기(초)
            button_3x3_seconds=item.get('item_f051'),  # 3×3 버튼누르기(초)
            absolute_grip_strength_kg=item.get('item_f052'),  # 절대악력(kg)
            pres_note=item.get('pres_note')  # 운동처방내용
        )
    
    async def _check_items_exist_batch(self, items: List[Dict[str, Any]], db: AsyncSession) -> set:
        """
        여러 아이템의 존재 여부를 배치로 확인
        
        Args:
            items: 확인할 데이터 리스트
            db: 데이터베이스 세션
            
        Returns:
            이미 존재하는 아이템의 키 집합 (row_num, test_ym 조합)
        """
        if not items:
            return set()
        
        try:
            # 고유 키 추출
            keys = []
            for item in items:
                row_num = item.get('row_num')
                test_ym = item.get('test_ym')
                if row_num and test_ym:
                    keys.append((row_num, test_ym))
            
            if not keys:
                return set()
            
            # 배치 조회
            conditions = []
            for row_num, test_ym in keys:
                conditions.append(
                    and_(
                        PhysicalFitnessResult.row_num == row_num,
                        PhysicalFitnessResult.test_ym == test_ym
                    )
                )
            
            if conditions:
                query = select(PhysicalFitnessResult.row_num, PhysicalFitnessResult.test_ym).where(
                    or_(*conditions)
                )
                result = await db.execute(query)
                existing_keys = {(row_num, test_ym) for row_num, test_ym in result.fetchall()}
                return existing_keys
            
            return set()
        except Exception as e:
            logger.error(f"배치 중복 체크 실패: {e}")
            return set()

    async def _fetch_page_data(
        self,
        page_no: int,
        num_of_rows: int,
        age_class: Optional[str] = None,
        age_gbn: Optional[str] = None,
        cert_gbn: Optional[str] = None,
        start_test_ym: Optional[str] = None,
        end_test_ym: Optional[str] = None,
        test_sex: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """단일 페이지 데이터 가져오기"""
        data = await self.fetch_data_from_api(
            page_no=page_no,
            num_of_rows=num_of_rows,
            age_class=age_class,
            age_gbn=age_gbn,
            cert_gbn=cert_gbn,
            start_test_ym=start_test_ym,
            end_test_ym=end_test_ym,
            test_sex=test_sex
        )
        return self._parse_api_response(data)

    async def load_all_data_from_api(
        self,
        max_pages: Optional[int] = None,
        num_of_rows: int = 100,
        age_class: Optional[str] = None,
        age_gbn: Optional[str] = None,
        cert_gbn: Optional[str] = None,
        start_test_ym: Optional[str] = None,
        end_test_ym: Optional[str] = None,
        test_sex: Optional[str] = None,
        concurrent_requests: int = 5,
        batch_size: int = 500,
        force_refresh: bool = False
    ) -> tuple[int, int]:
        """
        API에서 모든 데이터를 가져와서 DB에 저장 (병렬 처리 및 배치 저장)

        Args:
            max_pages: 최대 페이지 수 (None이면 전체)
            num_of_rows: 한 페이지 결과 수
            age_class: 측정자연령대
            age_gbn: 측정자연령구분
            cert_gbn: 상장구분
            start_test_ym: 시작측정년월
            end_test_ym: 종료측정년월
            test_sex: 측정자성별
            concurrent_requests: 동시 API 요청 수
            batch_size: 배치 저장 크기
            force_refresh: True이면 DB에 데이터가 있어도 강제로 다시 가져옴

        Returns:
            (저장된 개수, 스킵된 개수) 튜플
        """
        start_time = time.time()
        saved_count = 0
        skipped_count = 0
        
        logger.info("=" * 80)
        logger.info("체력 측정 결과 데이터 수집 시작")
        if force_refresh:
            logger.info("⚠ 강제 새로고침 모드: DB에 데이터가 있어도 다시 가져옵니다.")
        logger.info(f"설정: 동시 요청 수={concurrent_requests}, 배치 크기={batch_size}, 페이지당 항목 수={num_of_rows}")
        logger.info("=" * 80)
        
        # DB에 이미 데이터가 있는지 확인
        logger.info("DB에 저장된 데이터 확인 중...")
        try:
            async with AsyncSessionLocal() as db:
                try:
                    count_query = select(func.count(PhysicalFitnessResult.id))
                    result = await db.execute(count_query)
                    existing_count = result.scalar() or 0
                    
                    if existing_count > 0 and not force_refresh:
                        logger.info(f"✓ DB에 이미 {existing_count}개의 데이터가 존재합니다.")
                        logger.info("API 요청을 건너뜁니다. (강제 새로고침하려면 force_refresh=True 사용)")
                        logger.info("=" * 80)
                        return 0, existing_count
                    elif existing_count > 0 and force_refresh:
                        logger.info(f"⚠ DB에 이미 {existing_count}개의 데이터가 존재하지만, 강제 새로고침 모드로 진행합니다.")
                    else:
                        logger.info("✓ DB에 데이터가 없습니다. API에서 데이터를 가져옵니다.")
                except Exception as e:
                    logger.error(f"✗ DB 쿼리 중 오류 발생: {e}")
                    logger.exception(e)
                    raise
        except Exception as e:
            error_msg = str(e)
            logger.error("=" * 80)
            logger.error("✗ RDS 데이터베이스 연결 실패")
            logger.error("=" * 80)
            logger.error(f"오류 메시지: {error_msg}")
            
            # 오류 타입에 따른 상세 가이드
            if "Access denied" in error_msg or "1045" in error_msg:
                logger.error("")
                logger.error("가능한 원인:")
                logger.error("1. RDS 보안 그룹(Security Group) 설정:")
                logger.error(f"   - 현재 접속 IP (15.164.135.137)에서 RDS로의 접근이 허용되어 있는지 확인")
                logger.error("   - AWS 콘솔 > RDS > 보안 그룹 > 인바운드 규칙에서 MySQL/Aurora 포트(3306) 허용 확인")
                logger.error("")
                logger.error("2. 데이터베이스 비밀번호:")
                logger.error("   - production.env 파일의 DATABASE_URL 비밀번호가 올바른지 확인")
                logger.error("   - RDS 마스터 비밀번호와 일치하는지 확인")
                logger.error("")
                logger.error("3. MySQL 사용자 호스트 제한:")
                logger.error("   - 'admin' 사용자가 '%' 또는 해당 IP에서 접근 가능하도록 설정되어 있는지 확인")
                logger.error("   - MySQL: SELECT user, host FROM mysql.user WHERE user='admin'; 명령으로 확인")
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.error("")
                logger.error("가능한 원인:")
                logger.error("1. RDS 보안 그룹에서 현재 IP의 접근이 차단되어 있음")
                logger.error("2. RDS 엔드포인트 주소가 올바른지 확인")
            else:
                logger.error("")
                logger.error("상세 오류 정보:")
                logger.exception(e)
            
            logger.error("=" * 80)
            logger.warning("⚠ DB 연결 실패로 인해 데이터 수집을 건너뜁니다.")
            logger.warning("⚠ DB 연결 문제를 해결한 후 서버를 재시작하거나, force_refresh=True로 강제 실행하세요.")
            logger.error("=" * 80)
            # 연결 실패 시 0, 0을 반환하여 서버는 계속 실행되도록 함
            return 0, 0
        
        # 먼저 첫 페이지로 전체 개수 확인
        logger.info("첫 페이지를 가져와서 전체 데이터 크기 확인 중...")
        logger.info(f"API URL: {settings.public_data_api_base_url}/TODZ_NFA_TEST_RESULT_NEW")
        first_page_start = time.time()
        try:
            first_items, total_count = await self._fetch_page_data(
                1, num_of_rows, age_class, age_gbn, cert_gbn, start_test_ym, end_test_ym, test_sex
            )
            first_page_time = time.time() - first_page_start
            logger.info(f"✓ 첫 페이지 수집 완료 (소요 시간: {first_page_time:.2f}초, 항목 수: {len(first_items)}, 전체 개수: {total_count})")
        except Exception as e:
            logger.error(f"✗ 첫 페이지 수집 실패: {e}")
            logger.exception(e)
            return 0, 0
        
        if not first_items:
            logger.warning("첫 페이지에 데이터가 없습니다.")
            return 0, 0
        
        # 전체 페이지 수 계산
        total_pages = (total_count + num_of_rows - 1) // num_of_rows
        if max_pages:
            total_pages = min(total_pages, max_pages)
        
        logger.info("=" * 80)
        logger.info(f"총 {total_pages}페이지, 예상 데이터 개수: {total_count}개")
        logger.info(f"병렬 처리로 {total_pages - 1}개 페이지 수집 시작 (동시 요청: {concurrent_requests}개)")
        logger.info("=" * 80)
        
        async with AsyncSessionLocal() as db:
            try:
                all_items = []
                
                # 첫 페이지 데이터 추가
                all_items.extend(first_items)
                logger.info(f"[페이지 1/1] 완료 - 누적 항목: {len(all_items)}개")
                
                # 나머지 페이지들을 병렬로 가져오기
                semaphore = asyncio.Semaphore(concurrent_requests)
                fetch_start_time = time.time()
                fetched_pages = 0
                failed_pages = 0
                
                async def fetch_page_with_semaphore(page: int):
                    nonlocal fetched_pages, failed_pages
                    async with semaphore:
                        page_start = time.time()
                        try:
                            await asyncio.sleep(0.1 * (page % concurrent_requests))  # API 제한 고려한 스태거
                            items, _ = await self._fetch_page_data(
                                page, num_of_rows, age_class, age_gbn, cert_gbn,
                                start_test_ym, end_test_ym, test_sex
                            )
                            page_time = time.time() - page_start
                            fetched_pages += 1
                            logger.info(f"[페이지 {page}/{total_pages}] 완료 - 항목: {len(items)}개 "
                                       f"(소요: {page_time:.2f}초, 진행률: {fetched_pages}/{total_pages - 1})")
                            return items
                        except Exception as e:
                            failed_pages += 1
                            logger.error(f"[페이지 {page}/{total_pages}] 실패 - {str(e)}")
                            return []
                
                # 병렬로 페이지 가져오기
                if total_pages > 1:
                    tasks = [fetch_page_with_semaphore(page) for page in range(2, total_pages + 1)]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            failed_pages += 1
                            logger.error(f"페이지 가져오기 예외 발생: {result}")
                            continue
                        if isinstance(result, list):
                            all_items.extend(result)
                
                fetch_time = time.time() - fetch_start_time
                logger.info("=" * 80)
                logger.info(f"✓ 병렬 데이터 수집 완료")
                logger.info(f"  - 총 수집 항목: {len(all_items)}개")
                logger.info(f"  - 성공한 페이지: {fetched_pages + 1}개")
                logger.info(f"  - 실패한 페이지: {failed_pages}개")
                logger.info(f"  - 소요 시간: {fetch_time:.2f}초")
                logger.info(f"  - 평균 속도: {len(all_items) / fetch_time:.2f} 항목/초")
                logger.info("=" * 80)
                
                logger.info("DB 배치 저장 시작...")
                save_start_time = time.time()
                
                total_batches = (len(all_items) + batch_size - 1) // batch_size
                logger.info(f"총 {total_batches}개 배치로 나누어 저장 예정")
                
                # 배치로 중복 체크 및 저장
                for batch_idx, i in enumerate(range(0, len(all_items), batch_size), 1):
                    batch_start_time = time.time()
                    batch_items = all_items[i:i + batch_size]
                    
                    logger.info(f"[배치 {batch_idx}/{total_batches}] 처리 시작 - {len(batch_items)}개 항목")
                    
                    # 배치 중복 체크
                    check_start = time.time()
                    existing_keys = await self._check_items_exist_batch(batch_items, db)
                    check_time = time.time() - check_start
                    logger.info(f"  - 중복 체크 완료: {len(existing_keys)}개 중복 발견 (소요: {check_time:.2f}초)")
                    
                    # 새 데이터만 필터링
                    new_items = []
                    batch_skipped = 0
                    for item in batch_items:
                        row_num = item.get('row_num')
                        test_ym = item.get('test_ym')
                        if row_num and test_ym:
                            if (row_num, test_ym) not in existing_keys:
                                new_items.append(item)
                            else:
                                batch_skipped += 1
                        else:
                            new_items.append(item)  # 키가 없으면 저장 시도
                    
                    skipped_count += batch_skipped
                    
                    # 배치로 저장
                    if new_items:
                        save_items_start = time.time()
                        for item in new_items:
                            result = self._convert_item_to_model(item)
                            db.add(result)
                        
                        commit_start = time.time()
                        await db.commit()
                        commit_time = time.time() - commit_start
                        save_items_time = time.time() - save_items_start
                        
                        saved_count += len(new_items)
                        batch_time = time.time() - batch_start_time
                        
                        logger.info(f"  ✓ 저장 완료: {len(new_items)}개 저장, {batch_skipped}개 스킵")
                        logger.info(f"    - 모델 변환+추가: {save_items_time - commit_time:.2f}초")
                        logger.info(f"    - DB 커밋: {commit_time:.2f}초")
                        logger.info(f"    - 배치 총 소요: {batch_time:.2f}초")
                        logger.info(f"    - 진행 상황: {min(i + batch_size, len(all_items))}/{len(all_items)} "
                                   f"(전체 저장: {saved_count}, 전체 스킵: {skipped_count})")
                    else:
                        batch_time = time.time() - batch_start_time
                        logger.info(f"  - 스킵: 이 배치의 모든 항목이 이미 존재함 (소요: {batch_time:.2f}초)")
                    
                    logger.info("")  # 빈 줄로 구분
                
                save_time = time.time() - save_start_time
                total_time = time.time() - start_time
                
                logger.info("=" * 80)
                logger.info("✓ 체력 측정 결과 데이터 로딩 완료")
                logger.info(f"  - 저장된 항목: {saved_count}개")
                logger.info(f"  - 스킵된 항목: {skipped_count}개")
                logger.info(f"  - 총 수집 항목: {len(all_items)}개")
                logger.info("=" * 80)
                logger.info("성능 요약:")
                logger.info(f"  - API 수집 시간: {fetch_time:.2f}초 ({len(all_items) / fetch_time:.2f} 항목/초)")
                logger.info(f"  - DB 저장 시간: {save_time:.2f}초 ({saved_count / save_time:.2f} 항목/초)")
                logger.info(f"  - 총 소요 시간: {total_time:.2f}초")
                logger.info(f"  - 전체 평균 속도: {len(all_items) / total_time:.2f} 항목/초")
                logger.info("=" * 80)
                
            except Exception as e:
                logger.error(f"체력 측정 결과 데이터 로딩 실패: {e}")
                logger.exception(e)  # 상세 스택 트레이스
                await db.rollback()
                raise

        return saved_count, skipped_count


async def load_physical_fitness_data_from_api(max_pages: Optional[int] = None, force_refresh: bool = False):
    """
    공공데이터 API에서 체력 측정 결과 데이터를 로드하는 편의 함수
    
    Args:
        max_pages: 최대 페이지 수 (None이면 전체 데이터 로딩)
        force_refresh: True이면 DB에 데이터가 있어도 강제로 다시 가져옴
    """
    service = PhysicalFitnessService()
    return await service.load_all_data_from_api(max_pages=max_pages, num_of_rows=100, force_refresh=force_refresh)
