# Frontend API 레퍼런스

## 개요

GPU 가격 모니터링 시스템의 프론트엔드 API 레퍼런스 문서입니다.

**Base URL**: `http://localhost:8080/api`  
**Content-Type**: `application/json`  
**환경 변수**: `VITE_API_BASE_URL`

---

## 목차

1. [SKU API](#1-sku-api)
2. [Price Log API](#2-price-log-api)
3. [Market Signal API](#3-market-signal-api)
4. [Risk Alert API](#4-risk-alert-api)
5. [에러 코드](#5-에러-코드)
6. [데이터 모델](#6-데이터-모델)

---

## 1. SKU API

### 1.1 전체 SKU 조회

```
GET /api/skus
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| searchTerm | string | ❌ | 검색어 (제품명, SKU 코드) |
| category | string | ❌ | 카테고리 필터 |
| problemStockOnly | boolean | ❌ | 문제 재고만 조회 |
| page | number | ❌ | 페이지 번호 (0부터 시작) |
| size | number | ❌ | 페이지 크기 |
| sortBy | string | ❌ | 정렬 기준 필드 |
| sortDirection | string | ❌ | 정렬 방향 (ASC, DESC) |

**Response**: `PageResponse<SKUResponse>`

---

### 1.2 SKU 단건 조회

```
GET /api/skus/{id}
```

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | ✅ | SKU ID |

**Response**: `SKUResponse`

---

### 1.3 SKU 생성

```
POST /api/skus
```

**Request Body**: `SKURequest`

**Response**: `SKUResponse`

---

### 1.4 SKU 수정

```
PUT /api/skus/{id}
```

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | ✅ | SKU ID |

**Request Body**: `SKURequest`

**Response**: `SKUResponse`

---

### 1.5 SKU 삭제

```
DELETE /api/skus/{id}
```

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | ✅ | SKU ID |

**Response**: `void`

---

## 2. Price Log API

### 2.1 가격 이력 조회

```
GET /api/price-logs
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| skuId | number | ✅ | SKU ID |
| startDate | string | ❌ | 시작 날짜 (ISO 8601) |
| endDate | string | ❌ | 종료 날짜 (ISO 8601) |

**Response**: `PriceLogResponse[]`

---

### 2.2 최신 가격 조회

```
GET /api/price-logs/latest
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| skuId | number | ✅ | SKU ID |

**Response**: `LatestPriceResponse`

---

## 3. Market Signal API

### 3.1 커뮤니티 신호 조회

```
GET /api/market-signals
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| startDate | string | ❌ | 시작 날짜 (ISO 8601) |
| endDate | string | ❌ | 종료 날짜 (ISO 8601) |
| keyword | string | ❌ | 키워드 필터 |

**Response**: `MarketSignalResponse[]`

---

### 3.2 트렌딩 키워드 조회

```
GET /api/market-signals/trending
```

**Response**: `TrendingKeywordResponse[]`

---

## 4. Risk Alert API

### 4.1 위험 알림 조회

```
GET /api/risk-alerts
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| acknowledged | boolean | ❌ | 확인 상태 필터 |
| skuId | number | ❌ | SKU ID 필터 |

**Response**: `RiskAlertResponse[]`

---

### 4.2 위험 알림 확인

```
PUT /api/risk-alerts/{id}/acknowledge
```

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | ✅ | 알림 ID |

**Request Body**: `AcknowledgeAlertRequest`

**Response**: `RiskAlertResponse`

---

## 5. 에러 코드

### HTTP 상태 코드

| 코드 | 설명 | 메시지 |
|------|------|--------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 204 | No Content | 삭제 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 409 | Conflict | 중복된 리소스 |
| 500 | Internal Server Error | 서버 오류 |

### 에러 응답 형식

```json
{
    "message": "에러 메시지"
}
```

---

## 6. 데이터 모델

### 6.1 SKU 모델

#### SKURequest

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| skuCode | string | ✅ | SKU 코드 |
| productName | string | ✅ | 제품명 |
| category | string | ✅ | 카테고리 |
| currentStock | number | ✅ | 현재 재고 |
| safeStock | number | ✅ | 안전 재고 |
| dailyConsumptionRate | number | ✅ | 일일 소비율 |

#### SKUResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | SKU ID |
| skuCode | string | SKU 코드 |
| productName | string | 제품명 |
| category | string | 카테고리 |
| currentStock | number | 현재 재고 |
| safeStock | number | 안전 재고 |
| riskLevel | string | 위험 수준 (SAFE, WARNING, CRITICAL) |
| expectedShortageDate | string \| null | 예상 품절일 |
| createdAt | string | 생성일시 (ISO 8601) |
| updatedAt | string | 수정일시 (ISO 8601) |

#### PageResponse<T>

| 필드 | 타입 | 설명 |
|------|------|------|
| content | T[] | 페이지 데이터 |
| totalElements | number | 전체 요소 수 |
| totalPages | number | 전체 페이지 수 |
| size | number | 페이지 크기 |
| number | number | 현재 페이지 번호 (0부터 시작) |

---

### 6.2 Price Log 모델

#### PriceLogResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | 가격 로그 ID |
| skuId | number | SKU ID |
| price | number | 가격 (KRW) |
| source | string | 출처 (예: "다나와") |
| sourceUrl | string \| null | 출처 URL |
| recordedAt | string | 기록 일시 (ISO 8601) |
| priceChangePct | number \| null | 전주 대비 가격 변동률 (%) |
| createdAt | string | 생성일시 (ISO 8601) |

#### LatestPriceResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| skuId | number | SKU ID |
| price | number | 가격 (KRW) |
| source | string | 출처 |
| recordedAt | string | 기록 일시 (ISO 8601) |
| priceChangePct | number \| null | 전주 대비 가격 변동률 (%) |

---

### 6.3 Market Signal 모델

#### MarketSignalResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | 신호 ID |
| keyword | string | 키워드 |
| postTitle | string | 게시물 제목 |
| postUrl | string \| null | 게시물 URL |
| subreddit | string | 서브레딧명 |
| sentimentScore | number \| null | 감성 점수 |
| mentionCount | number | 언급 횟수 |
| date | string | 날짜 (ISO 8601) |
| createdAt | string | 생성일시 (ISO 8601) |

#### TrendingKeywordResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| keyword | string | 키워드 |
| mentionCount | number | 언급 횟수 |
| weekOverWeekGrowth | number | 주간 성장률 (%) |
| topPosts | TopPost[] | 상위 게시물 목록 |

#### TopPost

| 필드 | 타입 | 설명 |
|------|------|------|
| title | string | 게시물 제목 |
| url | string | 게시물 URL |
| subreddit | string | 서브레딧명 |

---

### 6.4 Risk Alert 모델

#### RiskAlertResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | 알림 ID |
| skuId | number | SKU ID |
| productName | string | 제품명 |
| riskIndex | number | 위험 지수 |
| threshold | number | 임계값 |
| contributingFactors | ContributingFactors | 기여 요인 |
| acknowledged | boolean | 확인 여부 |
| createdAt | string | 생성일시 (ISO 8601) |

#### ContributingFactors

| 필드 | 타입 | 설명 |
|------|------|------|
| priceChange | number | 가격 변동률 (%) |
| sentimentScore | number | 감성 점수 |
| newReleaseMentions | number | 신제품 언급 횟수 |

#### AcknowledgeAlertRequest

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| acknowledged | boolean | ✅ | 확인 여부 (항상 true) |

---

## 7. 환경 설정

### 개발 환경

```env
VITE_API_BASE_URL=http://localhost:8080/api
```

### 프로덕션 환경

```env
VITE_API_BASE_URL=https://api.yourdomain.com/api
```

---

## 8. 참고 사항

### 날짜/시간 형식
- 모든 날짜/시간은 ISO 8601 형식 사용
- 예시: `2024-01-15T10:30:00`

### 가격 단위
- 모든 가격은 KRW(원) 단위

### 페이징
- 페이지 번호는 0부터 시작
- 기본 페이지 크기: 20

### 에러 처리
- 모든 API는 자동으로 에러를 토스트로 표시
- 네트워크 에러 발생 시 자동 재시도 없음

### 인증
- 현재 버전에서는 인증 불필요
- 향후 JWT 토큰 기반 인증 추가 예정

---

## 9. API 클라이언트 사용법

### Import

```typescript
import { skuApi } from '@/api/skuApi';
import { priceApi } from '@/api/priceApi';
import { marketSignalApi } from '@/api/marketSignalApi';
import { riskAlertApi } from '@/api/riskAlertApi';
```

### 메서드 목록

#### SKU API
- `skuApi.getAll(params)` - 전체 SKU 조회
- `skuApi.getById(id)` - SKU 단건 조회
- `skuApi.create(data)` - SKU 생성
- `skuApi.update(id, data)` - SKU 수정
- `skuApi.delete(id)` - SKU 삭제

#### Price API
- `priceApi.getPriceLogs(params)` - 가격 이력 조회
- `priceApi.getLatestPrice(skuId)` - 최신 가격 조회

#### Market Signal API
- `marketSignalApi.getMarketSignals(params)` - 커뮤니티 신호 조회
- `marketSignalApi.getTrendingKeywords()` - 트렌딩 키워드 조회

#### Risk Alert API
- `riskAlertApi.getRiskAlerts(params)` - 위험 알림 조회
- `riskAlertApi.acknowledgeAlert(id)` - 위험 알림 확인

---

## 10. 버전 정보

| 항목 | 값 |
|------|-----|
| 문서 버전 | 1.0.0 |
| API 버전 | v1 |
| 최종 수정일 | 2024-01-25 |
| 작성자 | GPU Price Monitoring Team |

---

## 11. 변경 이력

### v1.0.0 (2024-01-25)
- 초기 버전 작성
- SKU API 명세 추가
- Price Log API 명세 추가
- Market Signal API 명세 추가
- Risk Alert API 명세 추가
