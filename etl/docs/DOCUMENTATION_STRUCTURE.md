# 문서 구조 정리

## 📁 최종 폴더 구조

```
etl/
├── docs/                                    # 📚 문서 폴더 (신규)
│   ├── README.md                           # 문서 인덱스
│   ├── DOCUMENTATION_STRUCTURE.md          # 이 파일
│   ├── guides/                             # 설치 및 설정 가이드
│   │   └── PSYCOPG2_INSTALLATION_GUIDE.md # psycopg2 설치 가이드
│   ├── testing/                            # 테스트 관련 문서
│   │   ├── MOCK_DETAILED_EXPLANATION.md   # Mock 테스팅 설명
│   │   └── mock_explanation.py            # Mock 예제 코드
│   └── completion/                         # 작업 완료 요약
│       └── TASK_8_COMPLETION_SUMMARY.md   # Task 8 완료 요약
│
├── extractors/                             # 데이터 추출 모듈
│   ├── __init__.py
│   ├── danawa_crawler.py
│   └── reddit_collector.py
│
├── transformers/                           # 데이터 변환 모듈
│   ├── __init__.py
│   ├── product_normalizer.py
│   ├── sku_matcher.py
│   └── price_analyzer.py                  # ✨ Task 8에서 생성
│
├── loaders/                                # 데이터 적재 모듈
│   └── __init__.py
│
├── tests/                                  # 테스트 파일
│   ├── __init__.py
│   ├── test_danawa_crawler.py
│   ├── test_reddit_collector.py
│   ├── test_product_normalizer.py
│   ├── test_sku_matcher.py
│   ├── test_db_connection.py
│   └── test_price_analyzer.py             # ✨ Task 8에서 생성
│
├── venv/                                   # Python 가상환경
├── __init__.py
├── config.py                               # 설정 관리
├── db_connection.py                        # DB 연결 풀
├── models.py                               # 데이터 모델
├── pytest.ini                              # pytest 설정
├── requirements.txt                        # Python 의존성
├── .env.template                           # 환경변수 템플릿
├── .gitignore
├── README.md                               # 프로젝트 개요
└── SETUP.md                                # 초기 설정 가이드
```

## 📝 문서 분류 기준

### 1. guides/ - 설치 및 설정 가이드
**목적:** 개발 환경 구축 및 설정 방법

**포함 문서:**
- `PSYCOPG2_INSTALLATION_GUIDE.md` - Docker PostgreSQL 환경에서 psycopg2 설치

**추가 예정:**
- 환경 변수 설정 가이드
- Docker 설정 가이드
- 배포 가이드

### 2. testing/ - 테스트 관련 문서
**목적:** 테스트 작성 방법 및 전략

**포함 문서:**
- `MOCK_DETAILED_EXPLANATION.md` - Mock 객체 사용법 상세 설명
- `mock_explanation.py` - Mock 사용 예제 코드

**추가 예정:**
- Property-based testing 가이드
- 통합 테스트 가이드
- 테스트 커버리지 리포트

### 3. completion/ - 작업 완료 요약
**목적:** 각 Task 완료 시 구현 내용 및 결과 기록

**포함 문서:**
- `TASK_8_COMPLETION_SUMMARY.md` - Task 8 (가격 분석) 완료 요약

**추가 예정:**
- Task 9 완료 요약 (커뮤니티 감성 분석)
- Task 10 완료 요약 (재고 위험 지수)
- 각 Phase 완료 요약

## 🎯 문서 작성 원칙

### 1. 명확성 (Clarity)
- 제목만 봐도 내용을 알 수 있도록
- 기술 용어는 처음 사용 시 설명 추가
- 코드 예제는 실행 가능하게

### 2. 완전성 (Completeness)
- 설치부터 실행까지 모든 단계 포함
- 일반적인 문제와 해결 방법 포함
- 관련 문서 링크 제공

### 3. 유지보수성 (Maintainability)
- 버전 정보 명시 (Python 3.13, psycopg2-binary 2.9.11 등)
- 날짜 기록 (작성일, 최종 수정일)
- 변경 이력 관리

### 4. 접근성 (Accessibility)
- 한글과 영어 적절히 혼용
- 다이어그램과 코드 예제 활용
- 단계별 설명으로 초보자도 이해 가능

## 📊 문서 현황

### ✅ 완료된 문서 (3개)

| 문서 | 분류 | 목적 | 상태 |
|------|------|------|------|
| PSYCOPG2_INSTALLATION_GUIDE.md | guides | psycopg2 설치 방법 | ✅ 완료 |
| MOCK_DETAILED_EXPLANATION.md | testing | Mock 테스팅 설명 | ✅ 완료 |
| TASK_8_COMPLETION_SUMMARY.md | completion | Task 8 완료 요약 | ✅ 완료 |

### 📝 추가 예정 문서

| 문서 | 분류 | 목적 | 우선순위 |
|------|------|------|----------|
| ENVIRONMENT_SETUP.md | guides | 전체 환경 설정 | 높음 |
| PROPERTY_TESTING_GUIDE.md | testing | PBT 작성 방법 | 중간 |
| INTEGRATION_TESTING.md | testing | 통합 테스트 | 중간 |
| TASK_9_COMPLETION_SUMMARY.md | completion | Task 9 요약 | 높음 |
| DEPLOYMENT_GUIDE.md | guides | 배포 가이드 | 낮음 |

## 🔄 문서 업데이트 프로세스

### 1. 새 Task 시작 시
- 관련 가이드 문서 확인
- 필요한 설정 문서 작성

### 2. Task 진행 중
- 발견한 문제와 해결 방법 기록
- 코드 예제 작성

### 3. Task 완료 시
- 완료 요약 문서 작성 (`completion/`)
- 관련 가이드 업데이트
- README.md 링크 추가

### 4. 정기 리뷰
- 문서 정확성 검증
- 오래된 정보 업데이트
- 사용자 피드백 반영

## 🔗 관련 문서

### 프로젝트 루트
- [etl/README.md](../README.md) - 프로젝트 개요
- [etl/SETUP.md](../SETUP.md) - 초기 설정

### 스펙 문서
- `.kiro/specs/gpu-price-etl/requirements.md` - 요구사항
- `.kiro/specs/gpu-price-etl/design.md` - 설계
- `.kiro/specs/gpu-price-etl/tasks.md` - 작업 목록

### Backend 문서
- `backend/docs/API_TEST_COMMANDS.md` - API 테스트
- `backend/docs/PROPERTY_BASED_TESTING_GUIDE.md` - PBT 가이드

## 📞 문의 및 기여

문서 관련 질문이나 개선 제안:
1. 이슈 등록
2. Pull Request 제출
3. 팀 채널에 문의

---

**작성일:** 2025-01-23  
**최종 수정일:** 2025-01-23  
**작성자:** Kiro AI Assistant
