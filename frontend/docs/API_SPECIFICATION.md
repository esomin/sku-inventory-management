# Frontend API 명세서

## 개요

이 문서는 GPU 가격 모니터링 시스템의 프론트엔드 API 클라이언트 명세를 정의합니다. 모든 API는 Spring Boot 백엔드와 통신하며, 기본 URL은 `http://localhost:8080/api` 입니다.

**Base URL**: `http://localhost:8080/api`  
**Content-Type**: `application/json`  
**환경 변수**: `VITE_API_BASE_URL`로 Base URL 변경 가능

---

## 목차

1. [SKU API](#1-sku-api)
2. [Price Log API](#2-price-log-api)
3. [Market Signal API](#3-market-signal-api)
4. [Risk Alert API](#4-risk-alert-api)
5. [공통 에러 처리](#5-공통-에러-처리)
6. [데이터 타입 정의](#6-데이터-타입-정의)

---

## 1. SKU API

SKU(재고 관리 단위) 제품의 CRUD 작업을 처리하는 API입니다.

### 1.1 전체 SKU 조회

**Endpoint**: `GET /api/skus`

**설명**: 필터링, 정렬, 페이징을 지원하는 SKU 목록 조회

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| searchTerm | string | 아니오 | 검색어 (제품명, SKU 코드) |
| category | string | 아니오 | 카테고리 필터 |
| problemStockOnly | boolean | 아니오 | 문제 재고만 조회 |
| page | number | 아니오 | 페이지 번호 (0부터 시작) |
| size | number | 아니오 | 페이지 크기 |
| sortBy | string | 아니오 | 정렬 기준 필드 |
| sortDirection | 'ASC' \| 'DESC' | 아니오 | 정렬 방향 |

**Response**: `PageResponse<SKUResponse>`

**예시**:
```typescript
// 요청
const response = await skuApi.getAll({
    category: '그래픽카드',
    page: 0,
    size: 20,
    sortBy: 'createdAt',
    sortDirection: 'DESC'
});

// 응답
{
    content: [
        {
            id: 1,
            skuCode: "GPU-RTX4070-001",
            productName: "ASUS RTX 4070 TUF Gaming",
            category: "그래픽카드",
            currentStock: 50,
            safeStock: 20,
            riskLevel: "SAFE",
            expectedShortageDate: null,
            createdAt: "2024-01-15T10:30:00",
            updatedAt: "2024-01-15T10:30:00"
        }
    ],
    totalElements: 100,
    totalPages: 5,
    size: 20,
    number: 0
}
```

---

### 1.2 SKU 단건 조회

**Endpoint**: `GET /api/skus/{id}`

**설명**: ID로 특정 SKU 조회

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | 예 | SKU ID |

**Response**: `SKUResponse`

**예시**:
```typescript
// 요청
const response = await skuApi.getById(1);

// 응답
{
    id: 1,
    skuCode: "GPU-RTX4070-001",
    productName: "ASUS RTX 4070 TUF Gaming",
    category: "그래픽카드",
    currentStock: 50,
    safeStock: 20,
    riskLevel: "SAFE",
    expectedShortageDate: null,
    createdAt: "2024-01-15T10:30:00",
    updatedAt: "2024-01-15T10:30:00"
}
```

---

### 1.3 SKU 생성

**Endpoint**: `POST /api/skus`

**설명**: 새로운 SKU 생성

**Request Body**: `SKURequest`

**Response**: `SKUResponse`

**예시**:
```typescript
// 요청
const response = await skuApi.create({
    skuCode: "GPU-RTX4070-002",
    productName: "MSI RTX 4070 Gaming X",
    category: "그래픽카드",
    currentStock: 30,
    safeStock: 15,
    dailyConsumptionRate: 2.5
});

// 응답
{
    id: 2,
    skuCode: "GPU-RTX4070-002",
    productName: "MSI RTX 4070 Gaming X",
    category: "그래픽카드",
    currentStock: 30,
    safeStock: 15,
    riskLevel: "SAFE",
    expectedShortageDate: null,
    createdAt: "2024-01-16T09:00:00",
    updatedAt: "2024-01-16T09:00:00"
}
```

---

### 1.4 SKU 수정

**Endpoint**: `PUT /api/skus/{id}`

**설명**: 기존 SKU 정보 수정

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | 예 | SKU ID |

**Request Body**: `SKURequest`

**Response**: `SKUResponse`

**예시**:
```typescript
// 요청
const response = await skuApi.update(2, {
    skuCode: "GPU-RTX4070-002",
    productName: "MSI RTX 4070 Gaming X",
    category: "그래픽카드",
    currentStock: 25,
    safeStock: 15,
    dailyConsumptionRate: 2.5
});
```

---

### 1.5 SKU 삭제

**Endpoint**: `DELETE /api/skus/{id}`

**설명**: SKU 삭제

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | 예 | SKU ID |

**Response**: `void`

**예시**:
```typescript
// 요청
await skuApi.delete(2);
```

---

## 2. Price Log API

GPU 가격 이력 및 추이 데이터를 조회하는 API입니다.

### 2.1 가격 이력 조회

**Endpoint**: `GET /api/price-logs`

**설명**: 특정 SKU의 가격 이력 조회 (날짜 범위 필터링 지원)

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| skuId | number | 예 | SKU ID |
| startDate | string | 아니오 | 시작 날짜 (ISO 8601 형식) |
| endDate | string | 아니오 | 종료 날짜 (ISO 8601 형식) |

**Response**: `PriceLogResponse[]`

**예시**:
```typescript
// 요청
const response = await priceApi.getPriceLogs({
    skuId: 1,
    startDate: '2024-01-01',
    endDate: '2024-03-31'
});

// 응답
[
    {
        id: 101,
        skuId: 1,
        price: 589000,
        source: "다나와",
        sourceUrl: "https://www.danawa.com/product/12345",
        recordedAt: "2024-01-15T09:00:00",
        priceChangePct: -2.5,
        createdAt: "2024-01-15T09:05:00"
    },
    {
        id: 102,
        skuId: 1,
        price: 579000,
        source: "다나와",
        sourceUrl: "https://www.danawa.com/product/12345",
        recordedAt: "2024-01-22T09:00:00",
        priceChangePct: -1.7,
        createdAt: "2024-01-22T09:05:00"
    }
]
```

---

### 2.2 최신 가격 조회

**Endpoint**: `GET /api/price-logs/latest`

**설명**: 특정 SKU의 최신 가격 조회

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| skuId | number | 예 | SKU ID |

**Response**: `LatestPriceResponse`

**예시**:
```typescript
// 요청
const response = await priceApi.getLatestPrice(1);

// 응답
{
    skuId: 1,
    price: 579000,
    source: "다나와",
    recordedAt: "2024-01-22T09:00:00",
    priceChangePct: -1.7
}
```

---

## 3. Market Signal API

Reddit 커뮤니티 신호 및 트렌드 데이터를 조회하는 API입니다.

### 3.1 커뮤니티 신호 조회

**Endpoint**: `GET /api/market-signals`

**설명**: 커뮤니티 신호 데이터 조회 (날짜 범위 및 키워드 필터링 지원)

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| startDate | string | 아니오 | 시작 날짜 (ISO 8601 형식) |
| endDate | string | 아니오 | 종료 날짜 (ISO 8601 형식) |
| keyword | string | 아니오 | 키워드 필터 |

**Response**: `MarketSignalResponse[]`

**예시**:
```typescript
// 요청
const response = await marketSignalApi.getMarketSignals({
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    keyword: 'New Release'
});

// 응답
[
    {
        id: 201,
        keyword: "New Release",
        postTitle: "RTX 5070 release date leaked!",
        postUrl: "https://reddit.com/r/nvidia/comments/abc123",
        subreddit: "nvidia",
        sentimentScore: 8.5,
        mentionCount: 15,
        date: "2024-01-15",
        createdAt: "2024-01-15T10:05:00"
    },
    {
        id: 202,
        keyword: "New Release",
        postTitle: "New GPU lineup coming soon",
        postUrl: "https://reddit.com/r/pcmasterrace/comments/def456",
        subreddit: "pcmasterrace",
        sentimentScore: 7.2,
        mentionCount: 8,
        date: "2024-01-20",
        createdAt: "2024-01-20T10:05:00"
    }
]
```

---

### 3.2 트렌딩 키워드 조회

**Endpoint**: `GET /api/market-signals/trending`

**설명**: 주간 성장률이 높은 트렌딩 키워드 및 관련 게시물 조회

**Response**: `TrendingKeywordResponse[]`

**예시**:
```typescript
// 요청
const response = await marketSignalApi.getTrendingKeywords();

// 응답
[
    {
        keyword: "New Release",
        mentionCount: 45,
        weekOverWeekGrowth: 125.5,
        topPosts: [
            {
                title: "RTX 5070 release date leaked!",
                url: "https://reddit.com/r/nvidia/comments/abc123",
                subreddit: "nvidia"
            },
            {
                title: "New GPU lineup coming soon",
                url: "https://reddit.com/r/pcmasterrace/comments/def456",
                subreddit: "pcmasterrace"
            },
            {
                title: "Nvidia announces new cards",
                url: "https://reddit.com/r/nvidia/comments/ghi789",
                subreddit: "nvidia"
            }
        ]
    },
    {
        keyword: "Price Drop",
        mentionCount: 32,
        weekOverWeekGrowth: 78.3,
        topPosts: [
            {
                title: "RTX 4070 prices dropping fast",
                url: "https://reddit.com/r/nvidia/comments/jkl012",
                subreddit: "nvidia"
            }
        ]
    }
]
```

---

## 4. Risk Alert API

재고 위험 알림을 조회하고 관리하는 API입니다.

### 4.1 위험 알림 조회

**Endpoint**: `GET /api/risk-alerts`

**설명**: 위험 알림 목록 조회 (확인 상태 필터링 지원)

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| acknowledged | boolean | 아니오 | 확인 상태 필터 (true: 확인됨, false: 미확인) |
| skuId | number | 아니오 | SKU ID 필터 |

**Response**: `RiskAlertResponse[]`

**예시**:
```typescript
// 요청
const response = await riskAlertApi.getRiskAlerts({
    acknowledged: false
});

// 응답
[
    {
        id: 301,
        skuId: 1,
        productName: "ASUS RTX 4070 TUF Gaming",
        riskIndex: 125.5,
        threshold: 100.0,
        contributingFactors: {
            priceChange: -5.2,
            sentimentScore: 8.5,
            newReleaseMentions: 15
        },
        acknowledged: false,
        createdAt: "2024-01-22T10:00:00"
    },
    {
        id: 302,
        skuId: 3,
        productName: "MSI RTX 4070 Ti Gaming X",
        riskIndex: 110.3,
        threshold: 100.0,
        contributingFactors: {
            priceChange: -3.8,
            sentimentScore: 7.2,
            newReleaseMentions: 12
        },
        acknowledged: false,
        createdAt: "2024-01-22T10:00:00"
    }
]
```

---

### 4.2 위험 알림 확인

**Endpoint**: `PUT /api/risk-alerts/{id}/acknowledge`

**설명**: 특정 위험 알림을 확인 처리

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | number | 예 | 알림 ID |

**Request Body**: `AcknowledgeAlertRequest`

**Response**: `RiskAlertResponse`

**예시**:
```typescript
// 요청
const response = await riskAlertApi.acknowledgeAlert(301);

// 응답
{
    id: 301,
    skuId: 1,
    productName: "ASUS RTX 4070 TUF Gaming",
    riskIndex: 125.5,
    threshold: 100.0,
    contributingFactors: {
        priceChange: -5.2,
        sentimentScore: 8.5,
        newReleaseMentions: 15
    },
    acknowledged: true,
    createdAt: "2024-01-22T10:00:00"
}
```

---

## 5. 공통 에러 처리

모든 API 클라이언트는 공통 에러 인터셉터를 사용하여 에러를 처리하고 사용자에게 토스트 알림을 표시합니다.

### 5.1 HTTP 상태 코드별 처리

| 상태 코드 | 설명 | 토스트 메시지 |
|----------|------|--------------|
| 400 | Bad Request | 서버에서 반환한 메시지 또는 "잘못된 요청입니다" |
| 404 | Not Found | API별 커스텀 메시지 (예: "가격 데이터를 찾을 수 없습니다") |
| 409 | Conflict | "중복된 SKU 코드입니다" (SKU API만 해당) |
| 500 | Internal Server Error | "서버 오류가 발생했습니다" |
| 기타 | Other Errors | "오류가 발생했습니다" |

### 5.2 네트워크 에러

- **요청 전송 실패**: "서버에 연결할 수 없습니다"
- **요청 설정 오류**: "요청 중 오류가 발생했습니다"

### 5.3 에러 응답 형식

```typescript
{
    message: string;  // 에러 메시지
}
```

---

## 6. 데이터 타입 정의

### 6.1 SKU 관련 타입

#### SKURequest
```typescript
interface SKURequest {
    skuCode: string;              // SKU 코드
    productName: string;          // 제품명
    category: string;             // 카테고리
    currentStock: number;         // 현재 재고
    safeStock: number;            // 안전 재고
    dailyConsumptionRate: number; // 일일 소비율
}
```

#### SKUResponse
```typescript
interface SKUResponse {
    id: number;                        // SKU ID
    skuCode: string;                   // SKU 코드
    productName: string;               // 제품명
    category: string;                  // 카테고리
    currentStock: number;              // 현재 재고
    safeStock: number;                 // 안전 재고
    riskLevel: string;                 // 위험 수준 (SAFE, WARNING, CRITICAL)
    expectedShortageDate: string | null; // 예상 품절일
    createdAt: string;                 // 생성일시 (ISO 8601)
    updatedAt: string;                 // 수정일시 (ISO 8601)
}
```

#### PageResponse<T>
```typescript
interface PageResponse<T> {
    content: T[];         // 페이지 데이터
    totalElements: number; // 전체 요소 수
    totalPages: number;    // 전체 페이지 수
    size: number;          // 페이지 크기
    number: number;        // 현재 페이지 번호 (0부터 시작)
}
```

---

### 6.2 Price Log 관련 타입

#### PriceLogResponse
```typescript
interface PriceLogResponse {
    id: number;                  // 가격 로그 ID
    skuId: number;               // SKU ID
    price: number;               // 가격 (KRW)
    source: string;              // 출처 (예: "다나와")
    sourceUrl: string | null;    // 출처 URL
    recordedAt: string;          // 기록 일시 (ISO 8601)
    priceChangePct: number | null; // 전주 대비 가격 변동률 (%)
    createdAt: string;           // 생성일시 (ISO 8601)
}
```

#### LatestPriceResponse
```typescript
interface LatestPriceResponse {
    skuId: number;               // SKU ID
    price: number;               // 가격 (KRW)
    source: string;              // 출처 (예: "다나와")
    recordedAt: string;          // 기록 일시 (ISO 8601)
    priceChangePct: number | null; // 전주 대비 가격 변동률 (%)
}
```

#### GetPriceLogsParams
```typescript
interface GetPriceLogsParams {
    skuId: number;        // SKU ID (필수)
    startDate?: string;   // 시작 날짜 (ISO 8601)
    endDate?: string;     // 종료 날짜 (ISO 8601)
}
```

---

### 6.3 Market Signal 관련 타입

#### MarketSignalResponse
```typescript
interface MarketSignalResponse {
    id: number;                  // 신호 ID
    keyword: string;             // 키워드
    postTitle: string;           // 게시물 제목
    postUrl: string | null;      // 게시물 URL
    subreddit: string;           // 서브레딧명
    sentimentScore: number | null; // 감성 점수
    mentionCount: number;        // 언급 횟수
    date: string;                // 날짜 (ISO 8601)
    createdAt: string;           // 생성일시 (ISO 8601)
}
```

#### TrendingKeywordResponse
```typescript
interface TrendingKeywordResponse {
    keyword: string;             // 키워드
    mentionCount: number;        // 언급 횟수
    weekOverWeekGrowth: number;  // 주간 성장률 (%)
    topPosts: {
        title: string;           // 게시물 제목
        url: string;             // 게시물 URL
        subreddit: string;       // 서브레딧명
    }[];
}
```

#### GetMarketSignalsParams
```typescript
interface GetMarketSignalsParams {
    startDate?: string;   // 시작 날짜 (ISO 8601)
    endDate?: string;     // 종료 날짜 (ISO 8601)
    keyword?: string;     // 키워드 필터
}
```

---

### 6.4 Risk Alert 관련 타입

#### RiskAlertResponse
```typescript
interface RiskAlertResponse {
    id: number;                  // 알림 ID
    skuId: number;               // SKU ID
    productName: string;         // 제품명
    riskIndex: number;           // 위험 지수
    threshold: number;           // 임계값
    contributingFactors: {       // 기여 요인
        priceChange?: number;         // 가격 변동률 (%)
        sentimentScore?: number;      // 감성 점수
        newReleaseMentions?: number;  // 신제품 언급 횟수
    };
    acknowledged: boolean;       // 확인 여부
    createdAt: string;           // 생성일시 (ISO 8601)
}
```

#### GetRiskAlertsParams
```typescript
interface GetRiskAlertsParams {
    acknowledged?: boolean; // 확인 상태 필터
    skuId?: number;         // SKU ID 필터
}
```

#### AcknowledgeAlertRequest
```typescript
interface AcknowledgeAlertRequest {
    acknowledged: boolean;  // 확인 여부 (항상 true)
}
```

---

## 7. 사용 예시

### 7.1 가격 추이 차트 데이터 가져오기

```typescript
import { priceApi } from '@/api/priceApi';

async function fetchPriceHistory(skuId: number) {
    try {
        const response = await priceApi.getPriceLogs({
            skuId,
            startDate: '2024-01-01',
            endDate: '2024-03-31'
        });
        
        const chartData = response.data.map(log => ({
            date: new Date(log.recordedAt),
            price: log.price,
            change: log.priceChangePct
        }));
        
        return chartData;
    } catch (error) {
        console.error('Failed to fetch price history:', error);
        return [];
    }
}
```

---

### 7.2 트렌딩 키워드 대시보드

```typescript
import { marketSignalApi } from '@/api/marketSignalApi';

async function fetchTrendingDashboard() {
    try {
        const response = await marketSignalApi.getTrendingKeywords();
        
        const trendingData = response.data.map(trend => ({
            keyword: trend.keyword,
            mentions: trend.mentionCount,
            growth: trend.weekOverWeekGrowth,
            isHighGrowth: trend.weekOverWeekGrowth > 50,
            topPosts: trend.topPosts.slice(0, 5)
        }));
        
        return trendingData;
    } catch (error) {
        console.error('Failed to fetch trending keywords:', error);
        return [];
    }
}
```

---

### 7.3 위험 알림 패널

```typescript
import { riskAlertApi } from '@/api/riskAlertApi';

async function fetchActiveAlerts() {
    try {
        const response = await riskAlertApi.getRiskAlerts({
            acknowledged: false
        });
        
        const alerts = response.data.map(alert => ({
            id: alert.id,
            product: alert.productName,
            riskIndex: alert.riskIndex,
            factors: alert.contributingFactors,
            createdAt: new Date(alert.createdAt)
        }));
        
        return alerts;
    } catch (error) {
        console.error('Failed to fetch alerts:', error);
        return [];
    }
}

async function acknowledgeAlert(alertId: number) {
    try {
        await riskAlertApi.acknowledgeAlert(alertId);
        // 알림 목록 새로고침
        await fetchActiveAlerts();
    } catch (error) {
        console.error('Failed to acknowledge alert:', error);
    }
}
```

---

## 8. 환경 설정

### 8.1 환경 변수

`.env` 파일에 다음 변수를 설정하세요:

```env
VITE_API_BASE_URL=http://localhost:8080/api
```

### 8.2 개발 환경

```env
VITE_API_BASE_URL=http://localhost:8080/api
```

### 8.3 프로덕션 환경

```env
VITE_API_BASE_URL=https://api.yourdomain.com/api
```

---

## 9. 버전 정보

- **문서 버전**: 1.0.0
- **API 버전**: v1
- **최종 수정일**: 2024-01-25
- **작성자**: GPU Price Monitoring Team

---

## 10. 참고 사항

1. 모든 날짜/시간은 ISO 8601 형식을 사용합니다 (예: `2024-01-15T10:30:00`)
2. 가격은 KRW(원) 단위입니다
3. 페이지 번호는 0부터 시작합니다
4. 모든 API는 자동으로 에러를 토스트로 표시합니다
5. 네트워크 에러 발생 시 자동으로 재시도하지 않으므로 필요시 클라이언트에서 구현해야 합니다
