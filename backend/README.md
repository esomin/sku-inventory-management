# SKU Inventory Management - Backend

Spring Boot 기반 재고(SKU) 관리 시스템 백엔드

## 기술 스택

- Java 21
- Spring Boot 3.2.1
- Spring Data JPA
- PostgreSQL 15
- Gradle
- Lombok

## 시작하기

### 사전 요구사항

- Java 21 이상
- Docker & Docker Compose

### 데이터베이스 시작

```bash
docker-compose up -d
```

PostgreSQL이 `localhost:5432`에서 실행됩니다.

### 애플리케이션 실행

```bash
./gradlew bootRun
```

애플리케이션이 `http://localhost:8080`에서 실행됩니다.

### 테스트 실행

```bash
./gradlew test
```

### 빌드

```bash
./gradlew build
```

## API 엔드포인트

백엔드 API는 `/api` 경로에서 제공됩니다.

- `POST /api/skus` - SKU 생성
- `GET /api/skus` - SKU 목록 조회
- `GET /api/skus/{id}` - SKU 상세 조회
- `PUT /api/skus/{id}` - SKU 수정
- `DELETE /api/skus/{id}` - SKU 삭제

## 데이터베이스 설정

- Database: `sku_inventory`
- Username: `postgres`
- Password: `postgres`
- Port: `5432`

설정은 `src/main/resources/application.yml`에서 변경할 수 있습니다.
