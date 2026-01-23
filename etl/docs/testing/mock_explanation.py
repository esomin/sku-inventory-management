"""
Mock 객체의 작동 원리 설명
"""

from unittest.mock import Mock

# ============================================
# 1. Mock 객체의 기본 동작
# ============================================

# Mock 객체 생성
fake_db = Mock()

# 어떤 속성이든 접근 가능 (자동으로 생성됨)
print(fake_db.execute_with_retry)  # <Mock name='mock.execute_with_retry' id='...'>
print(fake_db.any_method_name)     # <Mock name='mock.any_method_name' id='...'>
print(fake_db.foo.bar.baz)         # 중첩된 속성도 자동 생성

# ============================================
# 2. 반환값 설정 (return_value)
# ============================================

# 가짜 데이터베이스 응답 설정
fake_db.execute_with_retry.return_value = [
    (1_000_000.0,),
    (1_000_000.0,),
]

# 이제 호출하면 설정한 값을 반환
result = fake_db.execute_with_retry("SELECT * FROM prices")
print(result)  # [(1000000.0,), (1000000.0,)]

# ============================================
# 3. 예외 발생 시뮬레이션 (side_effect)
# ============================================

# 데이터베이스 에러 시뮬레이션
fake_db.execute_with_retry.side_effect = Exception("Connection failed")

try:
    fake_db.execute_with_retry("SELECT * FROM prices")
except Exception as e:
    print(f"에러 발생: {e}")  # "에러 발생: Connection failed"

# ============================================
# 4. 호출 여부 확인 (assert_called)
# ============================================

fake_db = Mock()
fake_db.execute_with_retry.return_value = []

# 함수 호출
fake_db.execute_with_retry("SELECT * FROM prices", (1, 2))

# 호출되었는지 확인
fake_db.execute_with_retry.assert_called_once()

# 특정 인자로 호출되었는지 확인
fake_db.execute_with_retry.assert_called_with("SELECT * FROM prices", (1, 2))

# ============================================
# 5. sys.modules를 이용한 모듈 모킹
# ============================================

import sys

# 가짜 psycopg2 모듈 생성
fake_psycopg2 = Mock()

# Python의 모듈 시스템에 가짜 모듈 등록
sys.modules['psycopg2'] = fake_psycopg2

# 이제 import psycopg2를 하면 가짜 모듈을 가져옴
import psycopg2  # ← 실제 psycopg2가 없어도 에러 안 남!
print(psycopg2)  # <Mock id='...'>

# ============================================
# 6. 실제 테스트에서의 사용 예시
# ============================================

def calculate_price_change(db, sku_id, current_price):
    """가격 변동률 계산 함수"""
    # DB에서 과거 가격 조회
    historical = db.execute_with_retry(
        "SELECT price FROM prices WHERE sku_id = %s",
        (sku_id,),
        fetch=True
    )
    
    if not historical:
        raise ValueError("No historical data")
    
    avg_price = sum(p[0] for p in historical) / len(historical)
    change = ((current_price - avg_price) / avg_price) * 100
    
    return round(change, 2)


# 테스트: 실제 DB 없이 로직만 검증
def test_price_change():
    # 가짜 DB 생성
    mock_db = Mock()
    
    # 가짜 DB가 반환할 데이터 설정
    mock_db.execute_with_retry.return_value = [
        (1_000_000.0,),
        (1_000_000.0,),
        (1_000_000.0,)
    ]
    
    # 함수 실행 (실제 DB 없이!)
    result = calculate_price_change(mock_db, sku_id=1, current_price=1_100_000.0)
    
    # 결과 검증
    assert result == 10.0, f"Expected 10.0, got {result}"
    
    # DB가 올바르게 호출되었는지 확인
    mock_db.execute_with_retry.assert_called_once()
    
    print("✅ 테스트 통과!")


# 테스트 실행
test_price_change()

# ============================================
# 7. Mock vs 실제 객체 비교
# ============================================

print("\n" + "="*50)
print("Mock vs 실제 객체 비교")
print("="*50)

# 실제 객체
class RealDatabase:
    def execute_with_retry(self, query, params, fetch=False):
        # 실제로는 PostgreSQL에 연결하고 쿼리 실행
        # 네트워크 I/O, 디스크 I/O 발생
        # 느리고 복잡함
        pass

# Mock 객체
mock_db = Mock()
mock_db.execute_with_retry.return_value = [(1000000.0,)]

# Mock의 장점:
# 1. 즉시 생성 (DB 연결 불필요)
# 2. 빠름 (네트워크 I/O 없음)
# 3. 제어 가능 (원하는 응답 설정)
# 4. 격리됨 (다른 테스트에 영향 없음)

print("\nMock 객체 특징:")
print("- 어떤 메서드든 호출 가능")
print("- 반환값을 자유롭게 설정")
print("- 예외도 시뮬레이션 가능")
print("- 호출 여부 추적 가능")
