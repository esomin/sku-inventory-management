# 구현 계획: GPU 가격 모니터링 ETL 시스템

## 개요

이 구현 계획은 GPU 가격 모니터링 ETL 시스템을 단계별로 구축하는 과정을 설명합니다. 기존 SKU 재고 관리 시스템을 GPU 특화로 확장하고, Python 기반 ETL 애플리케이션을 신규 개발하여 다나와/에누리 가격 데이터 및 Reddit 커뮤니티 신호를 수집·분석합니다.

## 구현 전략

### Phase 1: 마스터 데이터 정의 (Target SKUs)
RTX 4070 시리즈 칩셋 리스트를 기준으로 시스템을 구축합니다.
- RTX 4070
- RTX 4070 Super
- RTX 4070 Ti
- RTX 4070 Ti Super

### Phase 2: 다양한 소스에서의 매핑 실험 (Transform)
소스마다 제각각인 제품명을 정규화하여 하나의 SKU로 매핑합니다.

**예시:**
- 소스 A (다나와): "ASUS Dual 지포스 RTX 4070 SUPER O12G OC D6X 12GB"
- 소스 B (Reddit): "Got a great deal on a 4070 Super Dual today"

**정규화 결과:** `{BRAND: "ASUS", CHIPSET: "RTX 4070 Super", LINEUP: "Dual", VRAM: "12GB", OC: true}`

### Phase 3: 분석 로직 구현 (Insight)
가격 변동과 커뮤니티 신호를 결합하여 재고 위험을 조기 감지합니다.

**알람 조건 예시:**
- Reddit에서 "5070 release date" 키워드 빈도가 전주 대비 50% 상승
- 다나와 최저가가 5% 이상 하락
- → **[재고 처분 권고]** 신호 발생

## Tasks

### Phase 1: 백엔드 확장 - GPU 특화 SKU 엔티티

- [x] 1. 백엔드 SKU 엔티티 확장
  - [x] 1.1 SKU 엔티티에 GPU 특화 필드 추가
    - chipset (String) - RTX 4070 시리즈 칩셋명
    - brand (String) - 제조사 (ASUS, MSI, 이엠텍 등)
    - modelName (String) - 라인업명 (TUF, Gaming X, Dual 등)
    - vram (String) - VRAM 용량 (예: "12GB")
    - isOc (Boolean) - 오버클럭 여부
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 1.2 SKU 엔티티 유효성 검증 추가
    - chipset 필드는 RTX 4070 시리즈만 허용 (4070, 4070 Super, 4070 Ti, 4070 Ti Super)
    - category 필드는 "그래픽카드"로 고정
    - vram 필드는 숫자+단위 형식 검증 (예: "12GB")
    - _Requirements: 1.2, 1.3_
  
  - [x] 1.3 데이터베이스 마이그레이션 스크립트 작성
    - 기존 skus 테이블에 컬럼 추가 (chipset, brand, model_name, vram, is_oc)
    - 인덱스 추가 (chipset, brand)
    - _Requirements: 1.1_

- [x] 2. 백엔드 DTO 및 API 확장
  - [x] 2.1 SKURequest/SKUResponse DTO 확장
    - GPU 특화 필드 추가 (chipset, brand, modelName, vram, isOc)
    - 유효성 검증 어노테이션 추가
    - _Requirements: 1.1, 1.2_
  
  - [x] 2.2 SKUController API 엔드포인트 확장
    - GET /api/skus?chipset={chipset} - 칩셋별 필터링
    - GET /api/skus?brand={brand} - 브랜드별 필터링
    - GET /api/skus/compare?ids={id1,id2} - 모델 간 비교
    - _Requirements: 13.1, 13.2, 13.5_
  
  - [x] 2.3 SKUService 비즈니스 로직 확장
    - RTX 4070 시리즈 칩셋 검증 로직
    - 모델 간 가격 차이 계산 로직
    - _Requirements: 1.3, 13.4_

### Phase 2: 데이터베이스 스키마 확장

- [x] 3. 새로운 테이블 생성
  - [x] 3.1 Price_Logs 테이블 생성
    - id (BIGSERIAL PRIMARY KEY)
    - sku_id (BIGINT FOREIGN KEY → skus.id)
    - price (DECIMAL)
    - recorded_at (TIMESTAMP)
    - source_url (VARCHAR)
    - source_name (VARCHAR) - "다나와"
    - price_change_pct (DECIMAL) - 전주 대비 가격 변동률
    - 인덱스: (sku_id, recorded_at), (recorded_at)
    - _Requirements: 8.2, 5.1, 5.2_
  
  - [x] 3.2 Market_Signals 테이블 생성
    - id (BIGSERIAL PRIMARY KEY)
    - keyword (VARCHAR) - "New Release", "Price Drop" 등
    - sentiment_score (DECIMAL) - 감성 점수
    - mention_count (INTEGER) - 언급 횟수
    - date (DATE)
    - post_title (TEXT) - Reddit 게시물 제목
    - post_url (VARCHAR) - Reddit 게시물 URL
    - 인덱스: (keyword, date), (date)
    - _Requirements: 8.3, 6.1, 6.2_
  
  - [x] 3.3 Risk_Alerts 테이블 생성
    - id (BIGSERIAL PRIMARY KEY)
    - sku_id (BIGINT FOREIGN KEY → skus.id)
    - risk_index (DECIMAL) - 재고 위험 지수
    - alert_message (TEXT) - 알림 메시지
    - created_at (TIMESTAMP)
    - acknowledged (BOOLEAN) - 확인 여부
    - 인덱스: (sku_id, created_at), (acknowledged)
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

### Phase 3: Python ETL 애플리케이션 개발

- [x] 4. ETL 프로젝트 설정
  - [x] 4.1 Python 프로젝트 구조 생성
    - etl/ 디렉토리 생성
    - requirements.txt 작성 (requests, beautifulsoup4, feedparser, psycopg2, apscheduler, python-dotenv)
    - .env 파일 템플릿 작성 (DB 연결 정보, API 키 등)
    - config.py 작성 (설정 관리)
    - _Requirements: 8.1, 8.5, 9.1_
  
  - [x] 4.2 데이터베이스 연결 모듈 작성
    - db_connection.py - PostgreSQL 연결 풀 관리
    - 재시도 로직 구현 (최대 3회)
    - _Requirements: 8.5_

- [x] 5. Extract 모듈 - 가격 크롤러
  - [x] 5.1 다나와 크롤러 구현
    - extractors/danawa_crawler.py 작성
    - RTX 4070 시리즈 제품 검색 및 가격 수집
    - 최근 3개월 가격 추이 데이터 수집
    - 에러 핸들링 및 로깅
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [x] 5.2 크롤러 테스트
    - 실제 웹사이트에서 데이터 수집 테스트
    - 파싱 정확도 검증
    - _Requirements: 3.1_

- [x] 6. Extract 모듈 - Reddit 수집기
  - [x] 6.1 Reddit RSS 피드 수집기 구현
    - extractors/reddit_collector.py 작성
    - r/nvidia, r/pcmasterrace RSS 피드 파싱
    - 키워드 필터링: "New Release", "Leak", "Issues", "Price Drop", "Used Market", "5070 release date"
    - Rate limit 핸들링
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 6.2 Reddit 수집기 테스트
    - RSS 피드 파싱 테스트
    - 키워드 필터링 정확도 검증
    - _Requirements: 4.3, 4.4_

- [x] 7. Transform 모듈 - 제품명 정규화
  - [x] 7.1 제품명 파서 구현
    - transformers/product_normalizer.py 작성
    - 브랜드명 추출 (ASUS, MSI, 이엠텍, 기가바이트 등)
    - 칩셋 추출 (RTX 4070, 4070 Super, 4070 Ti, 4070 Ti Super)
    - VRAM 용량 추출 (12GB, 16GB 등)
    - OC 여부 판단 ("OC", "오버클럭" 키워드)
    - 라인업명 추출 (TUF, Gaming X, Dual 등)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 7.2 정규화 테스트 케이스 작성
    - 다나와 제품명 정규화 테스트
    - Reddit 텍스트 정규화 테스트
    - 엣지 케이스 테스트 (약어, 오타 등)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 7.3 SKU 매칭 로직 구현
    - 정규화된 데이터를 기반으로 기존 SKU와 매칭
    - 매칭 실패 시 새로운 SKU 생성 제안
    - _Requirements: 8.1_

- [x] 8. Transform 모듈 - 가격 분석
  - [x] 8.1 가격 변동률 계산 구현
    - transformers/price_analyzer.py 작성
    - 전주 대비 가격 변동률 계산 (현재가 vs 7일 전 평균가)
    - 히스토리 데이터 부족 시 경고 로그
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x] 8.2 가격 분석 테스트
    - 가격 변동률 계산 정확도 검증
    - 엣지 케이스 테스트 (데이터 부족, 가격 0 등)
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 9. Transform 모듈 - 커뮤니티 감성 분석
  - [x] 9.1 키워드 빈도 분석 구현
    - transformers/sentiment_analyzer.py 작성
    - 일별 키워드 언급 횟수 집계
    - 중복 카운트 방지 (동일 게시물 내 중복 키워드)
    - _Requirements: 6.1, 6.2_
  
  - [x] 9.2 감성 점수 계산 구현
    - 키워드별 가중치 적용: "New Release" (3x), "Price Drop" (2x), 기타 (1x)
    - 감성 점수 = Σ(키워드 빈도 × 가중치)
    - _Requirements: 6.3, 6.4_
  
  - [x] 9.3 감성 분석 테스트
    - 키워드 빈도 집계 정확도 검증
    - 감성 점수 계산 정확도 검증
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Transform 모듈 - 재고 위험 지수 계산
  - [x] 10.1 위험 지수 계산 로직 구현
    - transformers/risk_calculator.py 작성
    - 위험 지수 = (현재가 - 전주 평균가) + (신제품 언급 횟수 × 0.3)
    - 임계값 초과 시 high-risk 플래그 설정
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 10.2 위험 지수 테스트
    - 다양한 시나리오 테스트 (가격 하락 + 신제품 루머 등)
    - 임계값 검증
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 11. Load 모듈 - 데이터베이스 적재
  - [x] 11.1 Products 테이블 적재 로직
    - loaders/db_loader.py 작성
    - 정규화된 제품 데이터를 Products 테이블에 삽입
    - 중복 체크 (chipset + brand + model_name)
    - _Requirements: 8.1_
  
  - [x] 11.2 Price_Logs 테이블 적재 로직
    - 가격 데이터를 Price_Logs 테이블에 삽입
    - 중복 레코드 처리 (sku_id + recorded_at 기준 UPDATE)
    - _Requirements: 8.2, 8.4_
  
  - [x] 11.3 Market_Signals 테이블 적재 로직
    - Reddit 신호 데이터를 Market_Signals 테이블에 삽입
    - 중복 레코드 처리 (keyword + date 기준 UPDATE)
    - _Requirements: 8.3, 8.4_
  
  - [x] 11.4 Risk_Alerts 테이블 적재 로직
    - 위험 지수가 임계값을 초과하는 제품에 대한 알림 생성
    - 알림 메시지 포맷팅 (제품명, 위험 지수, 원인)
    - _Requirements: 12.1, 12.2_
  
  - [x] 11.5 데이터 적재 테스트
    - 각 테이블 삽입/업데이트 테스트
    - 트랜잭션 롤백 테스트
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 12. ETL 파이프라인 통합
  - [x] 12.1 ETL 메인 파이프라인 작성
    - main.py 작성
    - Extract → Transform → Load 순차 실행
    - 각 단계별 에러 핸들링 및 로깅
    - _Requirements: 3.5, 8.5_
  
  - [x] 12.2 ETL 파이프라인 테스트
    - 전체 플로우 통합 테스트
    - 에러 시나리오 테스트
    - _Requirements: 3.5, 8.5_

- [x] 13. 스케줄러 구현
  - [x] 13.1 APScheduler 설정
    - scheduler.py 작성
    - 가격 크롤링 작업: 매일 오전 9시 실행
    - Reddit 수집 작업: 매일 오전 10시 실행
    - _Requirements: 9.1, 9.2_
  
  - [x] 13.2 CLI 명령어 구현
    - 수동 작업 트리거 명령어 (python main.py --task=price_crawl)
    - 스케줄러 시작/중지 명령어
    - _Requirements: 9.4_
  
  - [x] 13.3 스케줄러 테스트
    - 스케줄 실행 테스트
    - 작업 실패 시 로깅 검증
    - _Requirements: 9.1, 9.2, 9.3_

### Phase 4: 프론트엔드 확장

- [ ] 14. 프론트엔드 API 클라이언트 확장
  - [ ] 14.1 가격 추이 API 클라이언트 작성
    - api/priceApi.ts 작성
    - GET /api/price-logs?skuId={id}&startDate={date}&endDate={date}
    - GET /api/price-logs/latest?skuId={id}
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 14.2 커뮤니티 신호 API 클라이언트 작성
    - api/marketSignalApi.ts 작성
    - GET /api/market-signals?startDate={date}&endDate={date}
    - GET /api/market-signals/trending
    - _Requirements: 11.1, 11.2, 11.3_
  
  - [ ] 14.3 위험 알림 API 클라이언트 작성
    - api/riskAlertApi.ts 작성
    - GET /api/risk-alerts?acknowledged={boolean}
    - PUT /api/risk-alerts/{id}/acknowledge
    - _Requirements: 12.3, 12.4_

- [ ] 15. 백엔드 API 엔드포인트 구현
  - [ ] 15.1 PriceLogController 작성
    - GET /api/price-logs - 가격 로그 조회 (필터링, 페이징)
    - GET /api/price-logs/latest - 최신 가격 조회
    - _Requirements: 10.1, 10.2_
  
  - [ ] 15.2 MarketSignalController 작성
    - GET /api/market-signals - 커뮤니티 신호 조회 (필터링, 페이징)
    - GET /api/market-signals/trending - 트렌딩 키워드 조회
    - _Requirements: 11.1, 11.2_
  
  - [ ] 15.3 RiskAlertController 작성
    - GET /api/risk-alerts - 위험 알림 조회 (필터링, 페이징)
    - PUT /api/risk-alerts/{id}/acknowledge - 알림 확인 처리
    - _Requirements: 12.3, 12.4_

- [ ] 16. 프론트엔드 UI 컴포넌트 구현
  - [ ] 16.1 가격 추이 차트 컴포넌트
    - components/PriceChart.tsx 작성
    - Recharts 또는 Chart.js 사용
    - 최근 3개월 가격 추이 라인 차트
    - 다나와 데이터 표시
    - 호버 시 상세 정보 툴팁
    - 날짜 범위 필터
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  
  - [ ] 16.2 커뮤니티 트렌드 대시보드
    - components/TrendDashboard.tsx 작성
    - 최근 30일 키워드 언급 횟수 바 차트
    - 전주 대비 50% 이상 증가한 키워드 하이라이트
    - 키워드 클릭 시 관련 Reddit 게시물 상위 5개 표시
    - 24시간마다 자동 새로고침
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [ ] 16.3 위험 알림 패널
    - components/RiskAlertPanel.tsx 작성
    - 활성 알림 목록 표시
    - 알림 확인 버튼
    - 알림 히스토리 보기
    - _Requirements: 12.3, 12.4_
  
  - [ ] 16.4 RTX 4070 시리즈 비교 테이블
    - components/ModelComparisonTable.tsx 작성
    - 4070 시리즈 모델 나란히 비교
    - 현재가, 전주 대비 변동률, 위험 지수 표시
    - Super 모델 출시 시 일반 모델 가격 하락 하이라이트
    - 모델 간 가격 차이 계산 및 표시
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [ ] 16.5 모델 간 가격 비교 차트
    - components/ModelComparisonChart.tsx 작성
    - 두 모델 선택 시 가격 추이 오버레이 차트
    - _Requirements: 13.5_

- [ ] 17. 프론트엔드 메인 페이지 통합
  - [ ] 17.1 대시보드 레이아웃 구성
    - pages/Dashboard.tsx 작성
    - 위험 알림 패널 (상단)
    - RTX 4070 시리즈 비교 테이블 (중앙)
    - 가격 추이 차트 (하단 좌측)
    - 커뮤니티 트렌드 대시보드 (하단 우측)
    - _Requirements: 10.1, 11.1, 12.3, 13.1_
  
  - [ ] 17.2 네비게이션 및 필터 추가
    - 칩셋별 필터 (4070, 4070 Super, 4070 Ti, 4070 Ti Super)
    - 브랜드별 필터
    - 날짜 범위 선택
    - _Requirements: 10.4, 13.1_

### Phase 5: 통합 및 테스트

- [ ] 18. 엔드투엔드 통합
  - [ ] 18.1 전체 시스템 통합 테스트
    - PostgreSQL Docker 컨테이너 시작
    - Spring Boot 백엔드 시작
    - Python ETL 스케줄러 시작
    - React 프론트엔드 시작
    - _Requirements: 8.5, 9.1_
  
  - [ ] 18.2 ETL 파이프라인 실행 검증
    - 가격 크롤링 → 정규화 → 적재 → 프론트엔드 표시
    - Reddit 수집 → 감성 분석 → 적재 → 대시보드 표시
    - 위험 지수 계산 → 알림 생성 → 프론트엔드 알림
    - _Requirements: 3.1, 4.1, 4.2, 7.1, 12.1_
  
  - [ ] 18.3 알람 조건 시나리오 테스트
    - "5070 release date" 키워드 빈도 50% 상승 시뮬레이션
    - 다나와 최저가 5% 하락 시뮬레이션
    - [재고 처분 권고] 알림 발생 검증
    - _Requirements: 7.1, 7.2, 12.1, 12.2_

- [ ] 19. 문서화 및 배포 준비
  - [ ] 19.1 README 작성
    - 시스템 개요
    - 설치 및 실행 방법
    - ETL 작업 수동 실행 방법
    - 환경 변수 설정 가이드
  
  - [ ] 19.2 Docker Compose 설정
    - PostgreSQL, Spring Boot, React, Python ETL을 하나의 docker-compose.yml로 통합
    - 환경 변수 관리
  
  - [ ] 19.3 최종 체크포인트
    - 모든 요구사항 구현 확인
    - 모든 테스트 통과 확인
    - 사용자에게 최종 검토 요청

## 참고사항

- 각 작업은 특정 요구사항을 참조하여 추적 가능성을 보장합니다
- Phase 1-2는 기존 시스템 확장, Phase 3는 신규 ETL 앱 개발, Phase 4-5는 통합입니다
- Python ETL 앱은 독립적으로 실행 가능하며, 스케줄러를 통해 자동화됩니다
- 프론트엔드는 기존 React 앱을 확장하여 GPU 특화 대시보드를 추가합니다
- RTX 4070 시리즈로 범위를 한정하여 실험의 명확성을 확보합니다
