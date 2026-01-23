# Mock 객체 상세 설명

## 1. psycopg2 Import 문제 해결

### 문제 상황:
```python
# db_connection.py
import psycopg2  # ← psycopg2가 설치 안 되어 있으면 에러!
from psycopg2 import OperationalError, DatabaseError
```

### 해결 방법 (테스트에서):
```python
# test_price_analyzer.py
import sys
from unittest.mock import Mock

# Python의 모듈 시스템을 속임
sys.modules['psycopg2'] = Mock()  # ← 가짜 psycopg2 등록

# 이제 import psycopg2를 해도 에러 안 남
# Python은 sys.modules를 먼저 확인하기 때문
```

### Python의 Import 순서:
```
1. sys.modules 확인 (이미 로드된 모듈)
   └─> 있으면 그것 사용 ✅
   
2. sys.path에서 모듈 찾기
   └─> 없으면 ModuleNotFoundError ❌
```

우리는 1번 단계에서 가짜 모듈을 넣어서 2번으로 안 가게 만듦!

---

## 2. Mock 라이브러리

### 출처:
```python
from unittest.mock import Mock  # Python 표준 라이브러리 (3.3+)
```

**별도 설치 불필요!** Python에 기본 포함되어 있습니다.

### Mock 객체의 마법:

```python
mock = Mock()

# 1. 모든 속성 접근 가능 (자동 생성)
mock.anything        # ✅ 에러 없음
mock.foo.bar.baz     # ✅ 중첩도 가능
mock.method()        # ✅ 호출도 가능

# 2. 반환값 설정
mock.method.return_value = "Hello"
print(mock.method())  # "Hello"

# 3. 예외 발생
mock.method.side_effect = Exception("Error!")
mock.method()  # Exception 발생!
```

---

## 3. 가짜 DB Connection 만드는 과정

### 실제 코드 흐름:

```
테스트 시작
    ↓
sys.modules['psycopg2'] = Mock()  ← 1단계: 가짜 psycopg2 등록
    ↓
sys.modules['db_connection'] = Mock(db_manager=mock_db_manager)  ← 2단계: 가짜 db_connection 등록
    ↓
from transformers.price_analyzer import PriceAnalyzer  ← 3단계: import 시 가짜 모듈 사용
    ↓
analyzer = PriceAnalyzer()  ← 4단계: 가짜 db_manager 사용
    ↓
analyzer.db.execute_with_retry(...)  ← 5단계: 가짜 메서드 호출
    ↓
mock_db.execute_with_retry.return_value에서 설정한 값 반환  ← 6단계: 가짜 데이터 반환
```

### 상세 예시:

```python
# 테스트 코드
def test_calculate_price_change(self, analyzer, mock_db):
    # 1. 가짜 DB 설정
    analyzer.db = mock_db  # analyzer가 가짜 DB 사용하도록
    
    # 2. 가짜 DB의 응답 설정
    mock_db.execute_with_retry.return_value = [
        (1_000_000.0,),  # 첫 번째 가격
        (1_000_000.0,),  # 두 번째 가격
        (1_000_000.0,)   # 세 번째 가격
    ]
    
    # 3. 실제 함수 호출
    result = analyzer.calculate_price_change(sku_id=1, current_price=1_100_000.0)
    
    # 내부에서 일어나는 일:
    # analyzer.calculate_price_change() 실행
    #   ↓
    # self.db.execute_with_retry(...) 호출
    #   ↓
    # mock_db.execute_with_retry가 호출됨 (실제 DB 아님!)
    #   ↓
    # return_value에 설정한 값 반환: [(1000000.0,), (1000000.0,), (1000000.0,)]
    #   ↓
    # 평균 계산: 1,000,000
    #   ↓
    # 변동률 계산: (1,100,000 - 1,000,000) / 1,000,000 * 100 = 10%
    
    # 4. 결과 검증
    assert result == 10.0  # ✅ 통과!
```

---

## 4. Mock vs 실제 객체 비교

### 실제 DB 연결 (psycopg2 필요):
```python
import psycopg2  # ← 실제 설치 필요

conn = psycopg2.connect(
    host="localhost",
    database="gpu_etl",
    user="postgres",
    password="secret"
)

cursor = conn.cursor()
cursor.execute("SELECT price FROM prices WHERE sku_id = 1")
results = cursor.fetchall()  # 실제 DB에서 데이터 가져옴

# 특징:
# - PostgreSQL 서버 필요
# - 네트워크 I/O 발생
# - 느림 (수십~수백 ms)
# - 실제 데이터 필요
```

### Mock DB 연결 (psycopg2 불필요):
```python
from unittest.mock import Mock

mock_db = Mock()
mock_db.execute_with_retry.return_value = [
    (1_000_000.0,),
    (1_000_000.0,)
]

results = mock_db.execute_with_retry("SELECT price FROM prices WHERE sku_id = 1")
# results = [(1000000.0,), (1000000.0,)]

# 특징:
# - 아무것도 설치 안 해도 됨
# - 네트워크 I/O 없음
# - 매우 빠름 (< 1ms)
# - 원하는 데이터 자유롭게 설정
```

---

## 5. 왜 Mock을 사용하는가?

### 단위 테스트의 목적:
```
✅ 로직이 올바른가? (계산식, 조건문, 반복문)
❌ DB 연결이 되는가? (이건 통합 테스트에서)
```

### 예시:

```python
def calculate_price_change(db, sku_id, current_price):
    # 1. DB에서 데이터 가져오기 ← 이 부분은 Mock으로 대체
    historical = db.execute_with_retry(...)
    
    # 2. 계산 로직 ← 이 부분을 테스트하고 싶음!
    avg = sum(h[0] for h in historical) / len(historical)
    change = ((current_price - avg) / avg) * 100
    
    return round(change, 2)
```

**우리가 테스트하고 싶은 것**: 계산 로직 (2번)
**Mock으로 대체하는 것**: DB 접근 (1번)

### 장점:

1. **빠름**: 0.1초 vs 5초
2. **독립적**: PostgreSQL 설치 불필요
3. **제어 가능**: 에러 상황도 쉽게 테스트
4. **격리**: 다른 테스트에 영향 없음

---

## 6. 실제 프로젝트에서의 사용

```
개발 단계:
├── 단위 테스트 (현재)
│   ├── Mock 사용 ✅
│   ├── 로직만 검증
│   └── 빠르고 간단
│
├── 통합 테스트 (나중)
│   ├── 실제 psycopg2 사용 ✅
│   ├── DB 연결까지 검증
│   └── 느리지만 완전한 검증
│
└── 운영 환경
    ├── 실제 psycopg2 필수 ✅
    └── 실제 PostgreSQL 연결
```

---

## 7. 정리

### Q1: psycopg2가 필요한가?
- **단위 테스트**: 불필요 (Mock 사용)
- **통합 테스트**: 필요
- **운영 환경**: 필수

**✅ 해결됨:** Python 3.13에서는 최신 버전 사용 권장
```bash
# ❌ 특정 버전 지정 시 빌드 에러 발생
pip install psycopg2-binary==2.9.9

# ✅ 최신 버전 사용 (2.9.11+)
pip install psycopg2-binary
```

### Q2: Mock은 어떻게 가짜 DB를 만드는가?
```python
# 1. Mock 객체 생성
mock_db = Mock()

# 2. 원하는 응답 설정
mock_db.execute_with_retry.return_value = [(1000000.0,)]

# 3. 호출하면 설정한 값 반환
result = mock_db.execute_with_retry("SELECT ...")
# result = [(1000000.0,)]

# 실제 DB 연결 없이 "마치 DB에서 데이터를 가져온 것처럼" 동작!
```

### Q3: sys.modules는 무엇인가?
```python
# Python의 모듈 캐시
sys.modules['psycopg2'] = Mock()

# 이제 import psycopg2를 하면:
# 1. sys.modules에서 'psycopg2' 찾음
# 2. Mock 객체 발견!
# 3. 실제 psycopg2 설치 안 해도 에러 안 남
```

---

## 8. 실습 예제

```python
from unittest.mock import Mock

# 가짜 DB 생성
fake_db = Mock()

# 가짜 응답 설정
fake_db.get_price.return_value = 1_000_000

# 사용
price = fake_db.get_price(sku_id=1)
print(price)  # 1000000

# 호출 확인
fake_db.get_price.assert_called_once_with(sku_id=1)
print("✅ 테스트 통과!")
```

이제 Mock이 어떻게 작동하는지 이해되셨나요? 🎯
