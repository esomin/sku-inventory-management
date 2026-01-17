# 요구사항 문서

## 소개

재고(SKU) 관리 시스템은 제품 재고를 효율적으로 관리하고 모니터링하기 위한 웹 애플리케이션입니다. 사용자는 SKU(Stock Keeping Unit) 데이터를 생성, 조회, 수정, 삭제할 수 있으며, 검색 및 필터링 기능을 통해 재고 상태를 파악하고 품절 위험이 있는 재고를 식별할 수 있습니다.

## 용어 사전

- **System**: 재고(SKU) 관리 시스템
- **SKU**: Stock Keeping Unit, 재고 관리 단위
- **User**: 시스템을 사용하는 재고 관리자
- **Safe_Stock**: 안전 재고 수준, 최소한으로 유지해야 하는 재고량
- **Current_Stock**: 현재 재고 수량
- **Risk_Level**: 품절 위험 수준 (높음, 중간, 낮음)
- **Expected_Shortage_Date**: 예상 품절일, 재고가 부족해질 것으로 예상되는 날짜
- **Category**: 제품 카테고리
- **Problem_Stock**: 현재 재고가 안전 재고 이하이거나 품절 위험이 있는 재고

## 요구사항

### Requirement 1: SKU 데이터 생성

**User Story:** 재고 관리자로서, 새로운 SKU를 시스템에 등록하고 싶습니다. 그래야 재고를 추적하고 관리할 수 있습니다.

#### Acceptance Criteria

1. WHEN User가 유효한 SKU 정보를 제공하고 생성을 요청하면, THE System SHALL 새로운 SKU 레코드를 생성하고 데이터베이스에 저장한다
2. THE System SHALL SKU 코드, 제품명, 카테고리, 현재 재고, 안전 재고 필드를 필수로 요구한다
3. WHEN User가 중복된 SKU 코드로 생성을 시도하면, THE System SHALL 오류 메시지를 반환하고 생성을 거부한다
4. WHEN SKU가 성공적으로 생성되면, THE System SHALL 생성된 SKU의 고유 ID를 반환한다

### Requirement 2: SKU 데이터 조회

**User Story:** 재고 관리자로서, 등록된 SKU 목록을 조회하고 싶습니다. 그래야 현재 재고 상태를 파악할 수 있습니다.

#### Acceptance Criteria

1. WHEN User가 SKU 목록 조회를 요청하면, THE System SHALL 모든 SKU 데이터를 반환한다
2. THE System SHALL 각 SKU에 대해 SKU 코드, 제품명, 카테고리, 현재 재고, 안전 재고, 품절 위험, 예상 품절일을 포함한다
3. WHEN User가 특정 SKU ID로 조회를 요청하면, THE System SHALL 해당 SKU의 상세 정보를 반환한다
4. WHEN 존재하지 않는 SKU ID로 조회를 요청하면, THE System SHALL 404 오류를 반환한다

### Requirement 3: SKU 데이터 수정

**User Story:** 재고 관리자로서, 기존 SKU 정보를 수정하고 싶습니다. 그래야 재고 변동이나 정보 변경을 반영할 수 있습니다.

#### Acceptance Criteria

1. WHEN User가 유효한 SKU ID와 수정할 정보를 제공하면, THE System SHALL 해당 SKU 데이터를 업데이트한다
2. WHEN User가 SKU 코드를 다른 기존 SKU 코드로 변경하려고 하면, THE System SHALL 오류 메시지를 반환하고 수정을 거부한다
3. WHEN 존재하지 않는 SKU ID로 수정을 시도하면, THE System SHALL 404 오류를 반환한다
4. WHEN SKU가 성공적으로 수정되면, THE System SHALL 업데이트된 SKU 정보를 반환한다

### Requirement 4: SKU 데이터 삭제

**User Story:** 재고 관리자로서, 더 이상 관리하지 않는 SKU를 삭제하고 싶습니다. 그래야 시스템을 깔끔하게 유지할 수 있습니다.

#### Acceptance Criteria

1. WHEN User가 유효한 SKU ID로 삭제를 요청하면, THE System SHALL 해당 SKU를 데이터베이스에서 삭제한다
2. WHEN 존재하지 않는 SKU ID로 삭제를 시도하면, THE System SHALL 404 오류를 반환한다
3. WHEN SKU가 성공적으로 삭제되면, THE System SHALL 삭제 성공 응답을 반환한다

### Requirement 5: 검색 및 필터링

**User Story:** 재고 관리자로서, SKU를 검색하고 필터링하고 싶습니다. 그래야 원하는 재고를 빠르게 찾을 수 있습니다.

#### Acceptance Criteria

1. WHEN User가 검색어를 입력하면, THE System SHALL SKU 코드 또는 제품명에 검색어가 포함된 SKU 목록을 반환한다
2. WHEN User가 카테고리를 선택하면, THE System SHALL 해당 카테고리에 속한 SKU 목록만 반환한다
3. WHEN User가 "문제 재고 중점만 보기"를 활성화하면, THE System SHALL 현재 재고가 안전 재고 이하이거나 품절 위험이 있는 SKU만 반환한다
4. WHEN User가 여러 필터를 동시에 적용하면, THE System SHALL 모든 필터 조건을 만족하는 SKU만 반환한다
5. WHEN 검색 또는 필터 결과가 없으면, THE System SHALL 빈 목록을 반환한다

### Requirement 6: 정렬 기능

**User Story:** 재고 관리자로서, SKU 목록을 정렬하고 싶습니다. 그래야 데이터를 더 쉽게 분석할 수 있습니다.

#### Acceptance Criteria

1. WHEN User가 제품명 컬럼으로 정렬을 요청하면, THE System SHALL SKU 목록을 제품명 기준으로 오름차순 또는 내림차순으로 정렬한다
2. WHEN User가 예상 품절일 컬럼으로 정렬을 요청하면, THE System SHALL SKU 목록을 예상 품절일 기준으로 오름차순 또는 내림차순으로 정렬한다
3. THE System SHALL 정렬 방향(오름차순/내림차순)을 토글할 수 있어야 한다

### Requirement 7: 품절 위험 계산

**User Story:** 재고 관리자로서, 각 SKU의 품절 위험 수준을 자동으로 계산하고 싶습니다. 그래야 우선적으로 관리해야 할 재고를 식별할 수 있습니다.

#### Acceptance Criteria

1. WHEN 현재 재고가 안전 재고의 50% 미만이면, THE System SHALL 품절 위험을 "높음"으로 설정한다
2. WHEN 현재 재고가 안전 재고의 50% 이상 100% 미만이면, THE System SHALL 품절 위험을 "중간"으로 설정한다
3. WHEN 현재 재고가 안전 재고의 100% 이상이면, THE System SHALL 품절 위험을 "낮음"으로 설정한다
4. WHEN SKU 데이터가 조회되거나 수정되면, THE System SHALL 품절 위험을 자동으로 재계산한다

### Requirement 8: 예상 품절일 계산

**User Story:** 재고 관리자로서, 각 SKU의 예상 품절일을 확인하고 싶습니다. 그래야 재고 보충 계획을 세울 수 있습니다.

#### Acceptance Criteria

1. WHEN 현재 재고가 안전 재고보다 많으면, THE System SHALL 간단한 선형 계산을 사용하여 예상 품절일을 추정한다
2. WHEN 현재 재고가 안전 재고 이하이면, THE System SHALL 예상 품절일을 "즉시" 또는 현재 날짜로 설정한다
3. THE System SHALL 예상 품절일 계산에 일일 평균 소비량 가정을 사용한다
4. WHERE ML 예측 모델이 구현되면, THE System SHALL ML 모델의 예측 결과를 사용한다

### Requirement 9: 프론트엔드 UI

**User Story:** 재고 관리자로서, 직관적인 웹 인터페이스를 통해 재고를 관리하고 싶습니다. 그래야 효율적으로 작업할 수 있습니다.

#### Acceptance Criteria

1. THE System SHALL React와 Vite를 사용하여 프론트엔드를 구현한다
2. THE System SHALL shadcn/ui 컴포넌트 라이브러리를 사용하여 일관된 UI를 제공한다
3. WHEN 데이터가 로딩 중이면, THE System SHALL 로딩 인디케이터를 표시한다
4. WHEN 데이터가 없으면, THE System SHALL "No data" 메시지를 표시한다
5. THE System SHALL 반응형 디자인을 제공하여 다양한 화면 크기에서 사용 가능해야 한다

### Requirement 10: 백엔드 API

**User Story:** 시스템 아키텍트로서, RESTful API를 통해 프론트엔드와 백엔드를 분리하고 싶습니다. 그래야 시스템을 확장하고 유지보수하기 쉽습니다.

#### Acceptance Criteria

1. THE System SHALL Spring Boot를 사용하여 백엔드 API를 구현한다
2. THE System SHALL JPA를 사용하여 데이터베이스와 상호작용한다
3. THE System SHALL RESTful 원칙을 따르는 API 엔드포인트를 제공한다
4. WHEN API 요청이 실패하면, THE System SHALL 적절한 HTTP 상태 코드와 오류 메시지를 반환한다
5. THE System SHALL CORS를 설정하여 프론트엔드에서 API에 접근할 수 있도록 한다

### Requirement 11: 데이터 영속성

**User Story:** 시스템 아키텍트로서, 데이터를 안전하게 저장하고 관리하고 싶습니다. 그래야 데이터 손실을 방지할 수 있습니다.

#### Acceptance Criteria

1. THE System SHALL PostgreSQL 데이터베이스를 사용하여 SKU 데이터를 저장한다
2. THE System SHALL Docker를 사용하여 PostgreSQL을 실행한다
3. WHEN 데이터베이스 연결이 실패하면, THE System SHALL 오류를 로그에 기록하고 적절한 오류 응답을 반환한다
4. THE System SHALL 데이터베이스 스키마를 자동으로 생성하고 관리한다
