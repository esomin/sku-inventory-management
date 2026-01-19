# SKU 관리 시스템 API 테스트 명령어

이 문서는 SKU 관리 시스템의 API 엔드포인트를 테스트하기 위한 curl 명령어 모음입니다.

## 사전 준비

시스템을 실행하기 전에 다음 서비스들이 실행되어야 합니다:

1. **PostgreSQL Docker 컨테이너 시작**
```bash
cd backend
docker-compose up
```

2. **Spring Boot 백엔드 시작**
```bash
cd backend
./gradlew bootRun
```

3. **React 프론트엔드 시작** (별도 터미널)
```bash
cd frontend
npm run dev
```

## API 테스트 명령어

### 1. 기본 연결 확인

**빈 SKU 목록 조회**
```bash
curl -X GET http://localhost:8080/api/skus
```

### 2. SKU 생성 (CREATE)

**테스트 제품 1 생성 (품절 위험: 낮음)**
```bash
curl -X POST http://localhost:8080/api/skus \
  -H "Content-Type: application/json" \
  -d '{
    "skuCode": "TEST001",
    "productName": "테스트 제품 1",
    "category": "전자제품",
    "currentStock": 100,
    "safeStock": 50,
    "dailyConsumptionRate": 5.0
  }'
```

**테스트 제품 2 생성 (품절 위험: 높음)**
```bash
curl -X POST http://localhost:8080/api/skus \
  -H "Content-Type: application/json" \
  -d '{
    "skuCode": "TEST002",
    "productName": "테스트 제품 2",
    "category": "식품",
    "currentStock": 20,
    "safeStock": 100,
    "dailyConsumptionRate": 10.0
  }'
```

**영어 제품 생성 (품절 위험: 중간)**
```bash
curl -X POST http://localhost:8080/api/skus \
  -H "Content-Type: application/json" \
  -d '{
    "skuCode": "TEST003",
    "productName": "Electronics Product",
    "category": "Electronics",
    "currentStock": 75,
    "safeStock": 100,
    "dailyConsumptionRate": 3.0
  }'
```

### 3. SKU 조회 (READ)

**전체 SKU 목록 조회**
```bash
curl -X GET http://localhost:8080/api/skus
```

**특정 SKU 조회 (ID: 1)**
```bash
curl -X GET http://localhost:8080/api/skus/1
```

### 4. 검색 및 필터링

**검색어로 필터링 (SKU 코드/제품명)**
```bash
curl -X GET "http://localhost:8080/api/skus?searchTerm=TEST"
```

**카테고리로 필터링**
```bash
curl -X GET "http://localhost:8080/api/skus?category=Electronics"
```

**문제 재고만 조회 (현재 재고 ≤ 안전 재고)**
```bash
curl -X GET "http://localhost:8080/api/skus?problemStockOnly=true"
```

**복합 필터 (검색어 + 카테고리)**
```bash
curl -X GET "http://localhost:8080/api/skus?searchTerm=TEST&category=Electronics"
```

### 5. 정렬

**제품명 기준 내림차순 정렬**
```bash
curl -X GET "http://localhost:8080/api/skus?sortBy=productName&sortDirection=DESC"
```

**제품명 기준 오름차순 정렬**
```bash
curl -X GET "http://localhost:8080/api/skus?sortBy=productName&sortDirection=ASC"
```

**예상 품절일 기준 정렬**
```bash
curl -X GET "http://localhost:8080/api/skus?sortBy=expectedShortageDate&sortDirection=ASC"
```

### 6. 페이징

**페이지 크기 5, 첫 번째 페이지**
```bash
curl -X GET "http://localhost:8080/api/skus?page=0&size=5"
```

**페이지 크기 5, 두 번째 페이지**
```bash
curl -X GET "http://localhost:8080/api/skus?page=1&size=5"
```

### 7. SKU 수정 (UPDATE)

**SKU 정보 수정 (재고 증가)**
```bash
curl -X PUT http://localhost:8080/api/skus/1 \
  -H "Content-Type: application/json" \
  -d '{
    "skuCode": "TEST001",
    "productName": "수정된 테스트 제품 1",
    "category": "전자제품",
    "currentStock": 150,
    "safeStock": 50,
    "dailyConsumptionRate": 5.0
  }'
```

### 8. SKU 삭제 (DELETE)

**SKU 삭제**
```bash
curl -X DELETE http://localhost:8080/api/skus/3
```

### 9. 에러 케이스 테스트

**존재하지 않는 SKU 조회 (404 에러)**
```bash
curl -X GET http://localhost:8080/api/skus/999
```

**중복 SKU 코드 생성 시도 (409 에러)**
```bash
curl -X POST http://localhost:8080/api/skus \
  -H "Content-Type: application/json" \
  -d '{
    "skuCode": "TEST001",
    "productName": "중복 테스트",
    "category": "전자제품",
    "currentStock": 100,
    "safeStock": 50,
    "dailyConsumptionRate": 5.0
  }'
```

**존재하지 않는 SKU 수정 시도 (404 에러)**
```bash
curl -X PUT http://localhost:8080/api/skus/999 \
  -H "Content-Type: application/json" \
  -d '{
    "skuCode": "NONEXISTENT",
    "productName": "존재하지 않는 제품",
    "category": "테스트",
    "currentStock": 100,
    "safeStock": 50,
    "dailyConsumptionRate": 5.0
  }'
```

**존재하지 않는 SKU 삭제 시도 (404 에러)**
```bash
curl -X DELETE http://localhost:8080/api/skus/999
```

**잘못된 데이터 형식 (400 에러)**
```bash
curl -X POST http://localhost:8080/api/skus \
  -H "Content-Type: application/json" \
  -d '{
    "skuCode": "",
    "productName": "",
    "category": "",
    "currentStock": -1,
    "safeStock": -1,
    "dailyConsumptionRate": -1.0
  }'
```

## 품절 위험 계산 검증

시스템은 다음 규칙에 따라 품절 위험을 자동 계산합니다:

- **높음**: 현재 재고 < 안전 재고 × 0.5
- **중간**: 안전 재고 × 0.5 ≤ 현재 재고 < 안전 재고
- **낮음**: 현재 재고 ≥ 안전 재고

## 예상 품절일 계산 검증

시스템은 다음 규칙에 따라 예상 품절일을 자동 계산합니다:

- **현재 재고 ≤ 안전 재고**: 현재 날짜 (즉시)
- **현재 재고 > 안전 재고**: 현재 날짜 + ⌈(현재 재고 - 안전 재고) / 일일 소비량⌉일

## 응답 예시

### 성공적인 SKU 생성 응답
```json
{
  "id": 1,
  "skuCode": "TEST001",
  "productName": "테스트 제품 1",
  "category": "전자제품",
  "currentStock": 100,
  "safeStock": 50,
  "riskLevel": "낮음",
  "expectedShortageDate": "2026-01-29",
  "createdAt": "2026-01-19T16:44:42.730769",
  "updatedAt": "2026-01-19T16:44:42.730777"
}
```

### 에러 응답 예시
```json
{
  "timestamp": "2026-01-19T16:47:15.417403",
  "status": 404,
  "error": "Not Found",
  "message": "SKU를 찾을 수 없습니다: 999",
  "path": "/api/skus/999"
}
```

## 참고사항

- 한글 검색어나 카테고리를 사용할 때는 URL 인코딩이 필요할 수 있습니다
- 모든 날짜는 ISO 8601 형식으로 반환됩니다
- 페이징은 0부터 시작합니다 (첫 번째 페이지 = 0)
- 정렬 방향은 "ASC" (오름차순) 또는 "DESC" (내림차순)입니다