# psycopg2 설치 가이드 (Docker PostgreSQL 환경)

## 상황 분석

✅ **현재 환경:**
- PostgreSQL이 Docker 컨테이너로 실행 중 (`backend/docker-compose.yml`)
- ETL 애플리케이션은 Python으로 작성 (로컬에서 실행)
- ETL → Docker PostgreSQL 연결 필요

## 해결 방법

### Option 1: psycopg2-binary 설치 (권장 ⭐)

**장점:**
- PostgreSQL 서버 설치 불필요
- 컴파일 불필요 (바이너리 포함)
- 빠르고 간단

**설치 방법:**

```bash
cd etl  
source venv/bin/activate

# psycopg2-binary 최신 버전 설치 (Python 3.13 호환)
pip install psycopg2-binary
```

**⚠️ 중요:** Python 3.13에서는 특정 버전 지정 시 빌드 에러 발생
```bash
# ❌ 에러 발생 (pg_config not found)
pip install psycopg2-binary==2.9.9

# ✅ 성공 (최신 버전 자동 설치: 2.9.11+)
pip install psycopg2-binary
```

**왜 이게 가능한가?**
- `psycopg2-binary`는 PostgreSQL 클라이언트 라이브러리가 **이미 포함**되어 있음
- Docker PostgreSQL에 **네트워크로 연결**만 하면 됨
- 로컬에 PostgreSQL 서버 설치 불필요!

---

### Option 2: libpq 설치 후 psycopg2 설치 (대안)

만약 Option 1이 실패하면:

```bash
# 1. PostgreSQL 클라이언트 라이브러리만 설치
brew install libpq

# 2. PATH 설정
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/libpq/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libpq/include"

# 3. psycopg2 설치
pip install psycopg2==2.9.9
```

**차이점:**
- `libpq`: PostgreSQL **클라이언트** 라이브러리만 (서버 아님)
- 용량: ~10MB (전체 PostgreSQL 서버: ~200MB)

---

## 연결 설정

### 1. .env 파일 생성

```bash
cd etl
cp .env.template .env
```

### 2. .env 파일 수정

```bash
# Database Configuration (Docker PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sku_inventory
DB_USER=postgres
DB_PASSWORD=postgres

# Scheduler Configuration
PRICE_CRAWL_HOUR=9
PRICE_CRAWL_MINUTE=0
REDDIT_CRAWL_HOUR=10
REDDIT_CRAWL_MINUTE=0

# Risk Calculation
RISK_THRESHOLD=100.0
SENTIMENT_WEIGHT_NEW_RELEASE=3.0
SENTIMENT_WEIGHT_PRICE_DROP=2.0
SENTIMENT_WEIGHT_DEFAULT=1.0

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_SECONDS=5

# Logging
LOG_LEVEL=INFO
```

### 3. Docker PostgreSQL 실행

```bash
cd backend
docker-compose up -d postgres
```

### 4. 연결 테스트

```bash
cd etl
source venv/bin/activate
python -c "
from db_connection import db_manager
if db_manager.test_connection():
    print('✅ PostgreSQL 연결 성공!')
else:
    print('❌ PostgreSQL 연결 실패')
"
```

---

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                    macOS (로컬)                          │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  ETL Application (Python)                      │    │
│  │  ├── psycopg2-binary (클라이언트 라이브러리)    │    │
│  │  └── db_connection.py                          │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│                   │ TCP/IP (localhost:5432)              │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  Docker Container                              │    │
│  │  ┌──────────────────────────────────────────┐ │    │
│  │  │  PostgreSQL 15                           │ │    │
│  │  │  - Database: sku_inventory               │ │    │
│  │  │  - Port: 5432                            │ │    │
│  │  └──────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**핵심:**
- ETL은 로컬에서 실행
- PostgreSQL은 Docker에서 실행
- 네트워크로 연결 (localhost:5432)
- **PostgreSQL 서버를 macOS에 설치할 필요 없음!**

---

## 트러블슈팅

### 문제 1: psycopg2-binary 설치 실패

**증상:**
```
Error: pg_config executable not found.
```

**해결:**
```bash
# Python 버전 확인
python --version  # 3.13.9

# pip 업그레이드
pip install --upgrade pip

# wheel 설치
pip install wheel

# 다시 시도
pip install psycopg2-binary
```

### 문제 2: Docker PostgreSQL 연결 실패

**증상:**
```
psycopg2.OperationalError: could not connect to server
```

**해결:**
```bash
# 1. Docker 컨테이너 확인
docker ps | grep postgres

# 2. PostgreSQL 로그 확인
docker logs sku-inventory-postgres

# 3. 포트 확인
lsof -i :5432

# 4. Docker 재시작
cd backend
docker-compose restart postgres
```

### 문제 3: 권한 에러

**증상:**
```
psycopg2.OperationalError: FATAL: password authentication failed
```

**해결:**
```bash
# .env 파일의 비밀번호 확인
cat etl/.env | grep DB_PASSWORD

# docker-compose.yml의 비밀번호와 일치하는지 확인
cat backend/docker-compose.yml | grep POSTGRES_PASSWORD
```

---

## 최종 설치 스크립트

```bash
#!/bin/bash

echo "🚀 ETL 환경 설정 시작..."

# 1. 가상환경 활성화
cd etl
source venv/bin/activate

# 2. psycopg2-binary 설치
echo "📦 psycopg2-binary 설치 중..."
pip install psycopg2-binary

# 3. 나머지 의존성 설치
echo "📦 나머지 패키지 설치 중..."
pip install requests beautifulsoup4 lxml feedparser APScheduler python-dotenv pydantic pydantic-settings colorlog

# 4. .env 파일 생성
if [ ! -f .env ]; then
    echo "📝 .env 파일 생성 중..."
    cp .env.template .env
    echo "⚠️  .env 파일을 수정해주세요!"
fi

# 5. Docker PostgreSQL 시작
echo "🐳 Docker PostgreSQL 시작 중..."
cd ../backend
docker-compose up -d postgres

# 6. PostgreSQL 준비 대기
echo "⏳ PostgreSQL 준비 대기 중..."
sleep 5

# 7. 연결 테스트
echo "🔍 연결 테스트 중..."
cd ../etl
python -c "
from db_connection import db_manager
if db_manager.test_connection():
    print('✅ 설정 완료! PostgreSQL 연결 성공!')
else:
    print('❌ PostgreSQL 연결 실패. .env 파일을 확인해주세요.')
"

echo "🎉 완료!"
```

---

## 요약

### ✅ 해야 할 것:
1. `pip install psycopg2-binary` (간단!)
2. `.env` 파일 설정
3. `docker-compose up -d postgres`

### ❌ 하지 않아도 되는 것:
1. ~~PostgreSQL 서버를 macOS에 설치~~
2. ~~pg_config 설정~~
3. ~~복잡한 컴파일 과정~~

### 왜 이게 가능한가?
- Docker가 PostgreSQL **서버** 역할
- psycopg2-binary가 **클라이언트** 역할
- 네트워크로 연결만 하면 됨!

**결론: psycopg2-binary만 설치하면 끝! 🎯**
