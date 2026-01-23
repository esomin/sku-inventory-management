# ETL 프로젝트 문서

이 폴더는 GPU 가격 모니터링 ETL 시스템의 개발 문서를 포함합니다.

## 📁 폴더 구조

```
docs/
├── README.md                          # 이 파일
├── guides/                            # 설치 및 설정 가이드
│   └── PSYCOPG2_INSTALLATION_GUIDE.md # psycopg2 설치 가이드 (Docker 환경)
├── testing/                           # 테스트 관련 문서
│   ├── MOCK_DETAILED_EXPLANATION.md   # Mock 테스팅 상세 설명
│   └── mock_explanation.py            # Mock 사용 예제 코드
└── completion/                        # 작업 완료 요약
    └── TASK_8_COMPLETION_SUMMARY.md   # Task 8 완료 요약
```

## 📖 문서 목록

### 설치 가이드 (guides/)

#### [PSYCOPG2_INSTALLATION_GUIDE.md](guides/PSYCOPG2_INSTALLATION_GUIDE.md)
- Docker PostgreSQL 환경에서 psycopg2 설치 방법
- Python 3.13 호환성 문제 해결
- 연결 설정 및 트러블슈팅

**주요 내용:**
- psycopg2-binary 최신 버전 설치
- Docker PostgreSQL 연결 설정
- .env 파일 구성
- 일반적인 설치 문제 해결

### 테스트 문서 (testing/)

#### [MOCK_DETAILED_EXPLANATION.md](testing/MOCK_DETAILED_EXPLANATION.md)
- Mock 객체의 작동 원리
- 단위 테스트에서 Mock 사용법
- sys.modules를 이용한 모듈 모킹

**주요 내용:**
- Mock vs 실제 객체 비교
- 가짜 DB Connection 만드는 과정
- 테스트 전략 및 장점
- 실습 예제

#### [mock_explanation.py](testing/mock_explanation.py)
- Mock 사용법 실행 가능한 예제 코드
- 반환값 설정, 예외 발생, 호출 확인 등

### 완료 요약 (completion/)

#### [TASK_8_COMPLETION_SUMMARY.md](completion/TASK_8_COMPLETION_SUMMARY.md)
- Task 8 (가격 분석 모듈) 구현 완료 요약
- 구현 내용 및 테스트 결과
- 기술적 해결 사항
- 요구사항 검증

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

자세한 내용은 [PSYCOPG2_INSTALLATION_GUIDE.md](guides/PSYCOPG2_INSTALLATION_GUIDE.md)를 참조하세요.

### 2. 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_price_analyzer.py -v
```

테스트 작성 방법은 [MOCK_DETAILED_EXPLANATION.md](testing/MOCK_DETAILED_EXPLANATION.md)를 참조하세요.

## 📚 추가 자료

### 프로젝트 루트 문서
- `README.md` - 프로젝트 개요
- `SETUP.md` - 초기 설정 가이드
- `requirements.txt` - Python 의존성 목록

### 스펙 문서
- `.kiro/specs/gpu-price-etl/requirements.md` - 요구사항 명세
- `.kiro/specs/gpu-price-etl/design.md` - 설계 문서
- `.kiro/specs/gpu-price-etl/tasks.md` - 작업 목록

## 🤝 기여 가이드

새로운 문서를 추가할 때는 적절한 폴더에 배치해주세요:

- **설치/설정 가이드** → `guides/`
- **테스트 관련 문서** → `testing/`
- **작업 완료 요약** → `completion/`

## 📝 문서 작성 규칙

1. **명확한 제목**: 문서의 목적을 명확히 표현
2. **코드 예제**: 실행 가능한 예제 포함
3. **단계별 설명**: 복잡한 과정은 단계별로 설명
4. **트러블슈팅**: 일반적인 문제와 해결 방법 포함
5. **한글/영어 혼용**: 기술 용어는 영어, 설명은 한글

## 📞 문의

문서 관련 질문이나 개선 제안이 있으시면 이슈를 등록해주세요.
