# 구현 계획: 재고(SKU) 관리 시스템

## 개요

이 구현 계획은 재고(SKU) 관리 시스템을 단계별로 구축하는 과정을 설명합니다. 백엔드(Spring Boot + PostgreSQL)부터 시작하여 프론트엔드(React + Vite)를 구현하고, 마지막으로 통합 및 테스트를 수행합니다.

## Tasks

- [x] 1. 백엔드 프로젝트 설정 및 데이터베이스 구성
  - Spring Boot 프로젝트 생성 (Gradle, Java 21)
  - PostgreSQL Docker 설정 및 연결 구성
  - application.yml 설정 (데이터베이스, JPA, CORS)
  - _Requirements: 10.1, 10.2, 10.5, 11.1, 11.2_

- [x] 2. 백엔드 엔티티 및 리포지토리 구현
  - [x] 2.1 SKU 엔티티 클래스 작성
    - @Entity, @Table 어노테이션 설정
    - 모든 필드 정의 (id, skuCode, productName, category, currentStock, safeStock, dailyConsumptionRate, createdAt, updatedAt)
    - 유효성 검증 어노테이션 추가 (@NotNull, @NotBlank, @Min)
    - _Requirements: 1.2, 11.4_
  
  - [x] 2.2 SKURepository 인터페이스 작성
    - JpaRepository 상속
    - 커스텀 쿼리 메서드 정의 (findBySkuCode, existsBySkuCode, findWithFilters)
    - @Query 어노테이션으로 복잡한 필터링 쿼리 작성
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 3. 백엔드 DTO 및 예외 클래스 구현
  - [x] 3.1 DTO 클래스 작성
    - SKURequest DTO (유효성 검증 어노테이션 포함)
    - SKUResponse DTO
    - ErrorResponse DTO
    - _Requirements: 1.2, 2.2_
  
  - [x] 3.2 커스텀 예외 클래스 작성
    - SKUNotFoundException
    - DuplicateSKUException
    - _Requirements: 1.3, 2.4, 3.3, 4.2_

- [x] 4. 백엔드 서비스 레이어 구현
  - [x] 4.1 SKUService 인터페이스 및 구현체 작성
    - createSKU 메서드 (중복 체크 포함)
    - getSKUById 메서드
    - getAllSKUs 메서드 (페이징 및 필터링 지원)
    - updateSKU 메서드
    - deleteSKU 메서드
    - _Requirements: 1.1, 1.3, 2.1, 2.3, 3.1, 3.2, 4.1_
  
  - [x] 4.2 품절 위험 계산 로직 구현
    - calculateRiskLevel 메서드
    - 재고 비율에 따른 위험 수준 계산 (높음/중간/낮음)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 4.3 예상 품절일 계산 로직 구현
    - calculateExpectedShortageDate 메서드
    - 선형 계산 로직 구현 ((현재재고 - 안전재고) / 일일소비량)
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ]* 4.4 속성 테스트 작성 - 품절 위험 계산
    - **Property 12: 품절 위험 계산 정확성**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
  
  - [ ]* 4.5 속성 테스트 작성 - 예상 품절일 계산
    - **Property 13: 예상 품절일 계산 정확성**
    - **Validates: Requirements 8.1, 8.2, 8.3**

- [x] 5. 백엔드 컨트롤러 및 에러 핸들러 구현
  - [x] 5.1 SKUController 작성
    - POST /api/skus (SKU 생성)
    - GET /api/skus/{id} (SKU 조회)
    - GET /api/skus (SKU 목록 조회, 검색/필터/정렬/페이징 지원)
    - PUT /api/skus/{id} (SKU 수정)
    - DELETE /api/skus/{id} (SKU 삭제)
    - @CrossOrigin 설정
    - _Requirements: 1.1, 2.1, 2.3, 3.1, 4.1, 6.1, 6.2, 10.3, 10.5_
  
  - [x] 5.2 GlobalExceptionHandler 작성
    - @RestControllerAdvice 설정
    - SKUNotFoundException 핸들러 (404)
    - DuplicateSKUException 핸들러 (409)
    - MethodArgumentNotValidException 핸들러 (400)
    - 일반 Exception 핸들러 (500)
    - _Requirements: 10.4, 11.3_
  
  - [x] 5.3 속성 테스트 작성 - SKU CRUD 라운드트립
    - **Property 1: SKU 생성 라운드트립**
    - **Property 5: SKU 업데이트 라운드트립**
    - **Property 6: SKU 삭제 효과**
    - **Validates: Requirements 1.1, 1.4, 2.3, 3.1, 3.4, 4.1, 4.3**
  
  - [ ]* 5.4 단위 테스트 작성 - 에러 케이스
    - 중복 SKU 코드 테스트
    - 존재하지 않는 SKU 조회/수정/삭제 테스트
    - 유효하지 않은 입력 테스트
    - _Requirements: 1.3, 2.4, 3.3, 4.2_

- [x] 6. 체크포인트 - 백엔드 테스트 실행
  - 모든 테스트가 통과하는지 확인
  - 질문이 있으면 사용자에게 문의

- [ ]* 7. 백엔드 통합 테스트 작성
  - [ ]* 7.1 SKU CRUD 통합 테스트
    - MockMvc를 사용한 전체 플로우 테스트
    - 생성 → 조회 → 수정 → 삭제 시나리오
    - _Requirements: 1.1, 2.1, 2.3, 3.1, 4.1_
  
  - [ ]* 7.2 검색 및 필터링 통합 테스트
    - 검색어 필터 테스트
    - 카테고리 필터 테스트
    - 문제 재고 필터 테스트
    - 복합 필터 테스트
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 7.3 속성 테스트 작성 - 검색 및 필터링
    - **Property 7: 검색 필터 정확성**
    - **Property 8: 카테고리 필터 정확성**
    - **Property 9: 문제 재고 필터 정확성**
    - **Property 10: 복합 필터 정확성**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
  
  - [ ]* 7.4 속성 테스트 작성 - 정렬
    - **Property 11: 정렬 정확성**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 8. 프론트엔드 프로젝트 설정
  - Vite + React + TypeScript 프로젝트 생성
  - shadcn/ui 설치 및 설정
  - TanStack Query 설치
  - Axios 설치 및 설정
  - 프로젝트 구조 설정 (components, api, hooks, types)
  - _Requirements: 9.1, 9.2_

- [ ] 9. 프론트엔드 API 클라이언트 구현
  - [ ] 9.1 TypeScript 타입 정의
    - SKURequest 인터페이스
    - SKUResponse 인터페이스
    - PageResponse 인터페이스
    - _Requirements: 2.2_
  
  - [ ] 9.2 Axios API 클라이언트 작성
    - skuApi.ts 파일 생성
    - CRUD 메서드 구현 (getAll, getById, create, update, delete)
    - 에러 인터셉터 설정
    - _Requirements: 1.1, 2.1, 2.3, 3.1, 4.1_

- [ ] 10. 프론트엔드 UI 컴포넌트 구현
  - [ ] 10.1 SearchFilters 컴포넌트 작성
    - 검색 입력 필드
    - 카테고리 선택 드롭다운
    - "문제 재고 중점만 보기" 체크박스
    - 검색 버튼
    - shadcn/ui 컴포넌트 사용 (Input, Select, Checkbox, Button)
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ] 10.2 SKUTable 컴포넌트 작성
    - shadcn/ui Table 컴포넌트 사용
    - 모든 컬럼 표시 (SKU 코드, 제품명, 카테고리, 현재 재고, 안전 재고, 품절 위험, 예상 품절일, 작업)
    - 정렬 기능 구현 (제품명, 예상 품절일)
    - 페이지네이션 구현
    - 품절 위험 색상 표시 (높음: 빨강, 중간: 노랑, 낮음: 초록)
    - _Requirements: 2.2, 6.1, 6.2, 6.3_
  
  - [ ] 10.3 로딩 및 에러 상태 처리
    - 로딩 인디케이터 표시
    - "No data" 메시지 표시
    - 에러 메시지 표시 (toast 사용)
    - _Requirements: 9.3, 9.4_
  
  - [ ] 10.4 SKUForm 컴포넌트 작성 (생성/수정용)
    - 모든 필드 입력 폼
    - 유효성 검증
    - 생성/수정 모드 지원
    - Dialog 또는 Modal로 표시
    - _Requirements: 1.1, 1.2, 3.1_
  
  - [ ] 10.5 메인 페이지 통합
    - SearchFilters와 SKUTable 통합
    - TanStack Query 사용하여 데이터 페칭
    - 검색/필터 상태 관리
    - SKU 생성/수정/삭제 기능 연결
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 5.2, 5.3_

- [x]* 11. 체크포인트 - 프론트엔드 테스트
  - 개발 서버 실행 및 기능 확인
  - 질문이 있으면 사용자에게 문의

- [ ] 12. 프론트엔드 테스트 작성
  - [ ]* 12.1 컴포넌트 단위 테스트
    - SearchFilters 컴포넌트 테스트
    - SKUTable 컴포넌트 테스트
    - SKUForm 컴포넌트 테스트
    - React Testing Library 사용
    - _Requirements: 5.1, 5.2, 5.3, 9.3, 9.4_
  
  - [ ]* 12.2 속성 테스트 작성 - API 클라이언트
    - fast-check 사용
    - **Property 1: SKU 생성 라운드트립**
    - **Property 2: 필수 필드 검증**
    - **Property 3: 응답 완전성**
    - **Validates: Requirements 1.1, 1.2, 1.4, 2.2, 2.3**

- [ ] 13. 엔드투엔드 통합 및 최종 검증
  - [ ] 13.1 백엔드와 프론트엔드 동시 실행
    - PostgreSQL Docker 컨테이너 시작
    - Spring Boot 애플리케이션 시작
    - Vite 개발 서버 시작
    - _Requirements: 10.5, 11.2_
  
  - [ ] 13.2 전체 플로우 검증
    - SKU 생성 → 목록 조회 → 검색/필터 → 정렬 → 수정 → 삭제
    - 품절 위험 및 예상 품절일 자동 계산 확인
    - 에러 처리 확인
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 5.2, 5.3, 6.1, 6.2, 7.1, 7.2, 7.3, 8.1, 8.2_
  
  - [ ]* 13.3 속성 테스트 작성 - 에러 상태 코드
    - **Property 14: 에러 상태 코드 정확성**
    - **Validates: Requirements 10.4**

- [ ] 14. 최종 체크포인트
  - 모든 테스트가 통과하는지 확인
  - 모든 요구사항이 구현되었는지 확인
  - 질문이 있으면 사용자에게 문의

## 참고사항

- `*` 표시가 있는 작업은 선택적이며, 빠른 MVP를 위해 건너뛸 수 있습니다
- 각 작업은 특정 요구사항을 참조하여 추적 가능성을 보장합니다
- 체크포인트는 점진적 검증을 보장합니다
- 속성 테스트는 보편적 정확성 속성을 검증합니다
- 단위 테스트는 특정 예제 및 엣지 케이스를 검증합니다
