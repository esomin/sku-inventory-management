# 중복 제품 처리 정책 (Duplicate Handling Policy)

## 개요

ETL 파이프라인에서 데이터 적재 시 중복 레코드를 처리하는 정책을 정의합니다. 각 테이블은 고유한 비즈니스 요구사항에 따라 다른 ON CONFLICT 전략을 사용합니다.

## 1. Products 테이블 - 제품 정보

### 고유 키
```sql
UNIQUE(brand, model_name)
```

### 중복 처리 정책
**UPDATE** - 기존 제품 정보를 최신 데이터로 갱신

```sql
INSERT INTO products (category, chipset, brand, model_name, vram, is_oc, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (brand, model_name)
DO UPDATE SET
    chipset = EXCLUDED.chipset,
    vram = EXCLUDED.vram,
    is_oc = EXCLUDED.is_oc,
    updated_at = EXCLUDED.updated_at
RETURNING id
```

### 정책 선택 이유
- 같은 브랜드의 같은 모델명은 동일 제품으로 간주
- 제품 스펙이 변경되거나 데이터 정제 로직이 개선되면 최신 정보로 업데이트
- `updated_at` 타임스탬프로 마지막 갱신 시점 추적
- 제품 ID(sku_id)는 유지되어 외래 키 참조 무결성 보장

### 예시
```
기존 레코드:
  id: 1
  brand: "ASUS"
  model_name: "TUF Gaming OC"
  chipset: "RTX 4070"
  vram: "12GB"
  is_oc: true

신규 데이터:
  brand: "ASUS"
  model_name: "TUF Gaming OC"
  chipset: "RTX 4070 Super"  ← 변경됨
  vram: "12GB"
  is_oc: true

결과:
  → chipset이 "RTX 4070 Super"로 업데이트됨
  → id는 1로 유지됨
  → updated_at이 현재 시간으로 갱신됨
```

---

## 2. Price_Logs 테이블 - 가격 이력

### 고유 키
```sql
UNIQUE(sku_id, source, recorded_at)
```

### 중복 처리 정책
**UPDATE** - 같은 시점의 가격 데이터를 갱신

```sql
INSERT INTO price_logs (sku_id, price, source, source_url, recorded_at, price_change_pct)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (sku_id, source, recorded_at)
DO UPDATE SET
    price = EXCLUDED.price,
    source_url = EXCLUDED.source_url,
    price_change_pct = EXCLUDED.price_change_pct
```

### 정책 선택 이유
- 같은 제품, 같은 소스, 같은 시간의 가격은 중복으로 간주
- ETL 재실행 시 가격 변동률이 재계산되면 최신 값으로 업데이트
- 중복 레코드 방지로 데이터 정합성 유지
- 시계열 데이터의 일관성 보장

### 예시
```
기존 레코드:
  sku_id: 1
  source: "다나와"
  recorded_at: 2024-01-15 10:00:00
  price: 900000
  price_change_pct: -5.0

신규 데이터 (재실행 후 재계산):
  sku_id: 1
  source: "다나와"
  recorded_at: 2024-01-15 10:00:00
  price: 900000
  price_change_pct: -5.2  ← 재계산 결과

결과:
  → price_change_pct가 -5.2%로 업데이트됨
  → 중복 레코드 생성 방지
```

---

## 3. Market_Signals 테이블 - 커뮤니티 신호

### 고유 키
```sql
UNIQUE(keyword, date, post_url)
```

### 중복 처리 정책
**UPDATE + INCREMENT** - 언급 횟수 증가 및 최신 데이터 반영

```sql
INSERT INTO market_signals (keyword, post_title, post_url, subreddit, sentiment_score, date)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (keyword, date, post_url)
DO UPDATE SET
    post_title = EXCLUDED.post_title,
    sentiment_score = EXCLUDED.sentiment_score,
    mention_count = market_signals.mention_count + 1
```

### 정책 선택 이유
- 같은 날짜, 같은 키워드, 같은 게시물은 중복으로 간주
- ETL 재실행 시 `mention_count`를 증가시켜 재처리 횟수 추적
- 감성 점수는 최신 계산 결과로 업데이트 (분석 로직 개선 반영)
- 게시물 제목도 최신 버전으로 업데이트 (편집 반영)

### 예시
```
기존 레코드:
  keyword: "New Release"
  date: 2024-01-15
  post_url: "https://reddit.com/r/nvidia/comments/abc123"
  post_title: "RTX 5070 leaked specs"
  sentiment_score: 3.0
  mention_count: 1

신규 데이터 (ETL 재실행):
  keyword: "New Release"
  date: 2024-01-15
  post_url: "https://reddit.com/r/nvidia/comments/abc123"
  post_title: "RTX 5070 leaked specs [UPDATED]"  ← 편집됨
  sentiment_score: 3.5  ← 재계산됨

결과:
  → post_title이 "[UPDATED]" 버전으로 갱신됨
  → sentiment_score가 3.5로 갱신됨
  → mention_count가 2로 증가 (재처리 추적)
```

---

## 4. Risk_Alerts 테이블 - 위험 알림

### 고유 키
**없음** (중복 허용)

### 중복 처리 정책
**INSERT ONLY** - 항상 새로운 알림 생성

```sql
INSERT INTO risk_alerts (sku_id, risk_index, threshold, contributing_factors, acknowledged)
VALUES (%s, %s, %s, %s, %s)
-- ON CONFLICT 절 없음
```

### 정책 선택 이유
- 위험 지수가 임계값을 초과할 때마다 새로운 알림 생성
- 알림 히스토리를 모두 보존하여 위험 발생 패턴 분석 가능
- 시간에 따른 위험도 변화 추적
- `acknowledged` 플래그로 확인 여부만 관리
- 같은 제품에 대해 여러 알림이 존재할 수 있음 (시간대별)

### 예시
```
첫 번째 알림:
  created_at: 2024-01-15 10:00:00
  sku_id: 1
  risk_index: 120.0
  acknowledged: false

두 번째 알림 (4시간 후):
  created_at: 2024-01-15 14:00:00
  sku_id: 1
  risk_index: 150.0  ← 위험도 증가
  acknowledged: false

결과:
  → 두 알림 모두 보존됨 (중복 아님)
  → 위험도 증가 추세 분석 가능
  → 각각 독립적으로 확인 처리 가능
```

---

## 정책 비교 요약

| 테이블 | 고유 키 | 정책 | 주요 목적 |
|--------|---------|------|-----------|
| **Products** | `(brand, model_name)` | UPDATE | 제품 정보 최신 상태 유지 |
| **Price_Logs** | `(sku_id, source, recorded_at)` | UPDATE | 시계열 데이터 일관성 |
| **Market_Signals** | `(keyword, date, post_url)` | UPDATE + COUNT | 재처리 추적 + 최신 분석 |
| **Risk_Alerts** | 없음 | INSERT | 알림 히스토리 완전 보존 |

---

## 멱등성 보장 (Idempotency)

이러한 중복 처리 정책들은 ETL 파이프라인의 **멱등성(idempotency)**을 보장합니다:

### 멱등성이란?
같은 작업을 여러 번 실행해도 결과가 동일하게 유지되는 특성

### 보장 방법

1. **Products**: 같은 제품 데이터를 여러 번 적재해도 하나의 레코드만 존재
2. **Price_Logs**: 같은 시점의 가격을 여러 번 적재해도 하나의 레코드만 존재
3. **Market_Signals**: 같은 신호를 여러 번 적재해도 mention_count만 증가
4. **Risk_Alerts**: 알림은 시간별로 독립적이므로 멱등성 불필요

### 실무 적용 시나리오

**시나리오 1: ETL 작업 실패 후 재실행**
```
1차 실행: Products 10개 적재 → 5개 성공 후 실패
2차 실행: Products 10개 적재 → 기존 5개는 UPDATE, 나머지 5개는 INSERT
결과: 총 10개 제품 (중복 없음)
```

**시나리오 2: 데이터 정제 로직 개선 후 재실행**
```
1차 실행: 제품명 파싱 v1.0 → chipset 추출 정확도 80%
2차 실행: 제품명 파싱 v2.0 → chipset 추출 정확도 95%
결과: 모든 제품의 chipset이 v2.0 결과로 업데이트됨
```

**시나리오 3: 일일 배치 작업 중복 실행**
```
09:00 실행: 가격 데이터 100개 적재
09:30 실행: 같은 가격 데이터 100개 재적재 (실수)
결과: 100개 레코드만 존재 (중복 방지)
```

---

## 구현 위치

이 정책들은 다음 파일에 구현되어 있습니다:

- **코드**: `etl/loaders/db_loader.py`
- **테스트**: `etl/tests/test_db_loader.py`
- **스키마**: `backend/src/main/resources/db/migration/V*.sql`

---

## 주의사항

### Products 테이블
- `brand`와 `model_name`의 정규화가 중요
- 정규화 로직 변경 시 기존 데이터 재처리 필요

### Price_Logs 테이블
- `recorded_at`은 초 단위까지 정확해야 함
- 타임존 일관성 유지 필요 (UTC 권장)

### Market_Signals 테이블
- `mention_count` 증가는 재처리 추적용
- 실제 언급 횟수와 다를 수 있음 (재실행 시)

### Risk_Alerts 테이블
- 알림이 계속 쌓이므로 주기적인 정리 필요
- `acknowledged=true`인 오래된 알림 아카이빙 고려

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2024-01-24 | 1.0 | 초기 정책 문서 작성 |

