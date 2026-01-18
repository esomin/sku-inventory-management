# 속성 기반 테스트(Property-Based Testing) 가이드

## 목차
1. [개요](#개요)
2. [환경 설정](#환경-설정)
3. [테스트 작성 방법](#테스트-작성-방법)
4. [테스트 실행 방법](#테스트-실행-방법)
5. [예제 코드](#예제-코드)
6. [문제 해결](#문제-해결)

---

## 개요

### 속성 기반 테스트란?

속성 기반 테스트(Property-Based Testing, PBT)는 시스템이 모든 유효한 입력에 대해 만족해야 하는 보편적 속성을 검증하는 테스트 방법입니다.

**전통적인 단위 테스트 vs 속성 기반 테스트:**

```java
// 전통적인 단위 테스트 - 특정 예제
@Test
public void testCreateSKU() {
    SKURequest request = new SKURequest("SKU001", "제품A", "전자제품", 100, 50, 5.0);
    SKUResponse response = skuService.createSKU(request);
    assertEquals("SKU001", response.getSkuCode());
}

// 속성 기반 테스트 - 모든 유효한 입력
@Property(trials = 100)
public void skuCreationRoundTrip(@From(SKURequestGenerator.class) SKURequest request) {
    SKUResponse created = skuService.createSKU(request);
    SKUResponse retrieved = skuService.getSKUById(created.getId());
    assertEquals(request.getSkuCode(), retrieved.getSkuCode());
    // 100번의 랜덤 입력으로 자동 테스트
}
```

### 장점

- **광범위한 커버리지**: 수백 개의 랜덤 입력으로 자동 테스트
- **엣지 케이스 발견**: 개발자가 생각하지 못한 경우 자동 발견
- **명세 문서화**: 코드가 만족해야 하는 속성을 명확히 표현
- **회귀 방지**: 한 번 발견된 버그는 재현 가능

---

## 환경 설정

### 1. Gradle 의존성 추가

`build.gradle` 파일에 다음 의존성을 추가합니다:

```groovy
dependencies {
    // 기존 의존성...
    
    // Testing
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testRuntimeOnly 'com.h2database:h2'
    
    // JUnit 4 for Quickcheck compatibility
    testImplementation 'junit:junit:4.13.2'
    testRuntimeOnly 'org.junit.vintage:junit-vintage-engine'
    
    // JUnit Quickcheck for Property-Based Testing
    testImplementation 'com.pholser:junit-quickcheck-core:1.0'
    testImplementation 'com.pholser:junit-quickcheck-generators:1.0'
}

tasks.named('test') {
    useJUnitPlatform()
    testLogging {
        events "passed", "skipped", "failed"
        exceptionFormat "full"
    }
}
```

### 2. 테스트용 데이터베이스 설정

`src/test/resources/application-test.yml` 파일을 생성합니다:

```yaml
spring:
  application:
    name: sku-inventory-management-test
  
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
    username: sa
    password: 
  
  jpa:
    hibernate:
      ddl-auto: create-drop
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.H2Dialect
        format_sql: true
    open-in-view: false
  
  h2:
    console:
      enabled: false

server:
  port: 0
```

**설명:**
- H2 인메모리 데이터베이스 사용 (PostgreSQL 불필요)
- `create-drop`: 테스트마다 스키마 자동 생성/삭제
- `port: 0`: 랜덤 포트 사용 (충돌 방지)

---

## 테스트 작성 방법

### 1. 커스텀 제너레이터 작성

랜덤 테스트 데이터를 생성하는 제너레이터를 작성합니다.

**파일 위치:** `src/test/java/com/inventory/sku/generator/SKURequestGenerator.java`

```java
package com.inventory.sku.generator;

import com.inventory.sku.dto.SKURequest;
import com.pholser.junit.quickcheck.generator.GenerationStatus;
import com.pholser.junit.quickcheck.generator.Generator;
import com.pholser.junit.quickcheck.random.SourceOfRandomness;

import java.util.Arrays;
import java.util.List;

public class SKURequestGenerator extends Generator<SKURequest> {
    
    private static final List<String> CATEGORIES = Arrays.asList(
        "전자제품", "식품", "의류", "가구", "도서", "스포츠용품"
    );
    
    public SKURequestGenerator() {
        super(SKURequest.class);
    }
    
    @Override
    public SKURequest generate(SourceOfRandomness random, GenerationStatus status) {
        String skuCode = generateSKUCode(random);
        String productName = generateProductName(random);
        String category = CATEGORIES.get(random.nextInt(CATEGORIES.size()));
        Integer currentStock = random.nextInt(0, 1000);
        Integer safeStock = random.nextInt(0, 500);
        Double dailyConsumptionRate = random.nextDouble(0.0, 50.0);
        
        return new SKURequest(
            skuCode,
            productName,
            category,
            currentStock,
            safeStock,
            dailyConsumptionRate
        );
    }
    
    private String generateSKUCode(SourceOfRandomness random) {
        StringBuilder sb = new StringBuilder("SKU-");
        for (int i = 0; i < 5; i++) {
            if (random.nextBoolean()) {
                sb.append((char) ('A' + random.nextInt(26)));
            } else {
                sb.append(random.nextInt(10));
            }
        }
        return sb.toString();
    }
    
    private String generateProductName(SourceOfRandomness random) {
        String[] prefixes = {"프리미엄", "스탠다드", "베이직", "프로", "울트라"};
        String[] products = {"노트북", "마우스", "키보드", "모니터", "헤드셋"};
        
        return prefixes[random.nextInt(prefixes.length)] + " " + 
               products[random.nextInt(products.length)];
    }
}
```

**핵심 포인트:**
- `Generator<T>` 클래스를 상속
- `generate()` 메서드에서 랜덤 객체 생성
- 비즈니스 규칙에 맞는 유효한 데이터 생성
- 다양한 케이스를 커버하도록 범위 설정

### 2. 속성 테스트 클래스 작성

**파일 위치:** `src/test/java/com/inventory/sku/service/SKUServicePropertyTest.java`

```java
package com.inventory.sku.service;

import com.inventory.sku.dto.SKURequest;
import com.inventory.sku.dto.SKUResponse;
import com.inventory.sku.exception.SKUNotFoundException;
import com.inventory.sku.generator.SKURequestGenerator;
import com.pholser.junit.quickcheck.From;
import com.pholser.junit.quickcheck.Property;
import com.pholser.junit.quickcheck.runner.JUnitQuickcheck;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit4.rules.SpringClassRule;
import org.springframework.test.context.junit4.rules.SpringMethodRule;
import org.springframework.transaction.annotation.Transactional;

import static org.junit.Assert.*;

import org.junit.ClassRule;
import org.junit.Rule;

@RunWith(JUnitQuickcheck.class)
@SpringBootTest
@ActiveProfiles("test")
@Transactional
public class SKUServicePropertyTest {
    
    @ClassRule
    public static final SpringClassRule springClassRule = new SpringClassRule();
    
    @Rule
    public final SpringMethodRule springMethodRule = new SpringMethodRule();
    
    @Autowired
    private SKUService skuService;
    
    /**
     * Property 1: SKU 생성 라운드트립
     * 
     * 모든 유효한 SKU 요청에 대해, SKU를 생성한 후 해당 ID로 조회하면 
     * 동일한 데이터를 반환해야 한다.
     */
    @Property(trials = 100)
    public void skuCreationRoundTrip(@From(SKURequestGenerator.class) SKURequest request) {
        // Given: 유효한 SKU 요청
        
        // When: SKU를 생성하고 조회
        SKUResponse created = skuService.createSKU(request);
        SKUResponse retrieved = skuService.getSKUById(created.getId());
        
        // Then: 생성된 데이터와 조회된 데이터가 일치해야 함
        assertNotNull("생성된 SKU는 null이 아니어야 합니다", created);
        assertNotNull("생성된 SKU의 ID는 null이 아니어야 합니다", created.getId());
        
        assertEquals("SKU 코드가 일치해야 합니다", 
            request.getSkuCode(), retrieved.getSkuCode());
        assertEquals("제품명이 일치해야 합니다", 
            request.getProductName(), retrieved.getProductName());
        assertEquals("카테고리가 일치해야 합니다", 
            request.getCategory(), retrieved.getCategory());
        
        // Cleanup
        skuService.deleteSKU(created.getId());
    }
}
```

**핵심 어노테이션:**
- `@RunWith(JUnitQuickcheck.class)`: JUnit Quickcheck 러너 사용
- `@SpringBootTest`: Spring 컨텍스트 로드
- `@ActiveProfiles("test")`: 테스트 프로파일 활성화
- `@Transactional`: 각 테스트 후 롤백
- `@Property(trials = 100)`: 100번 반복 실행
- `@From(Generator.class)`: 커스텀 제너레이터 지정

### 3. 속성 정의 패턴

좋은 속성 테스트는 다음 패턴을 따릅니다:

#### 패턴 1: 라운드트립 (Round-trip)
```java
@Property(trials = 100)
public void roundTrip(@From(Generator.class) Input input) {
    Output output = service.create(input);
    Output retrieved = service.get(output.getId());
    assertEquals(input.getData(), retrieved.getData());
}
```

#### 패턴 2: 불변성 (Invariant)
```java
@Property(trials = 100)
public void invariant(@From(Generator.class) Input input) {
    Output output = service.process(input);
    assertTrue("결과는 항상 양수여야 함", output.getValue() >= 0);
}
```

#### 패턴 3: 멱등성 (Idempotence)
```java
@Property(trials = 100)
public void idempotence(@From(Generator.class) Input input) {
    Output first = service.process(input);
    Output second = service.process(input);
    assertEquals("같은 입력은 같은 결과를 반환", first, second);
}
```

#### 패턴 4: 역연산 (Inverse)
```java
@Property(trials = 100)
public void inverse(@From(Generator.class) Data data) {
    Data encoded = service.encode(data);
    Data decoded = service.decode(encoded);
    assertEquals("인코딩 후 디코딩하면 원본", data, decoded);
}
```

---

## 테스트 실행 방법

### 1. 전체 테스트 실행

```bash
cd backend
./gradlew test
```

### 2. 특정 테스트 클래스만 실행

```bash
./gradlew test --tests "com.inventory.sku.service.SKUServicePropertyTest"
```

### 3. 특정 속성 테스트만 실행

```bash
./gradlew test --tests "com.inventory.sku.service.SKUServicePropertyTest.skuCreationRoundTrip"
```

### 4. 상세 로그와 함께 실행

```bash
./gradlew test --info --tests "com.inventory.sku.service.SKUServicePropertyTest"
```

### 5. 테스트 결과 확인

테스트 실행 후 결과는 다음 위치에서 확인할 수 있습니다:

```
backend/build/reports/tests/test/index.html
```

브라우저로 열면 상세한 테스트 리포트를 볼 수 있습니다.

### 6. IDE에서 실행

**IntelliJ IDEA:**
1. 테스트 클래스 또는 메서드에서 우클릭
2. "Run 'SKUServicePropertyTest'" 선택
3. 또는 메서드 옆 초록색 화살표 클릭

**VS Code:**
1. Testing 패널 열기
2. 테스트 트리에서 실행할 테스트 선택
3. Run 버튼 클릭

---

## 예제 코드

### 예제 1: SKU 생성 라운드트립

```java
/**
 * Property: 생성 후 조회하면 동일한 데이터를 반환한다
 */
@Property(trials = 100)
public void skuCreationRoundTrip(@From(SKURequestGenerator.class) SKURequest request) {
    SKUResponse created = skuService.createSKU(request);
    SKUResponse retrieved = skuService.getSKUById(created.getId());
    
    assertEquals(request.getSkuCode(), retrieved.getSkuCode());
    assertEquals(request.getProductName(), retrieved.getProductName());
    assertEquals(request.getCategory(), retrieved.getCategory());
    assertEquals(request.getCurrentStock(), retrieved.getCurrentStock());
    assertEquals(request.getSafeStock(), retrieved.getSafeStock());
    
    skuService.deleteSKU(created.getId());
}
```

### 예제 2: SKU 업데이트 라운드트립

```java
/**
 * Property: 업데이트 후 조회하면 업데이트된 데이터를 반환한다
 */
@Property(trials = 100)
public void skuUpdateRoundTrip(
    @From(SKURequestGenerator.class) SKURequest initialRequest,
    @From(SKURequestGenerator.class) SKURequest updateRequest
) {
    SKUResponse created = skuService.createSKU(initialRequest);
    Long skuId = created.getId();
    
    // SKU 코드는 동일하게 유지 (중복 방지)
    updateRequest.setSkuCode(initialRequest.getSkuCode());
    
    SKUResponse updated = skuService.updateSKU(skuId, updateRequest);
    SKUResponse retrieved = skuService.getSKUById(skuId);
    
    assertEquals(updateRequest.getProductName(), retrieved.getProductName());
    assertEquals(updateRequest.getCategory(), retrieved.getCategory());
    assertEquals(updateRequest.getCurrentStock(), retrieved.getCurrentStock());
    
    skuService.deleteSKU(skuId);
}
```

### 예제 3: SKU 삭제 효과

```java
/**
 * Property: 삭제 후 조회하면 예외가 발생한다
 */
@Property(trials = 100)
public void skuDeletionEffect(@From(SKURequestGenerator.class) SKURequest request) {
    SKUResponse created = skuService.createSKU(request);
    Long skuId = created.getId();
    
    // 삭제 전에는 조회 가능
    SKUResponse beforeDelete = skuService.getSKUById(skuId);
    assertNotNull(beforeDelete);
    
    // 삭제
    skuService.deleteSKU(skuId);
    
    // 삭제 후 조회 시 예외 발생
    try {
        skuService.getSKUById(skuId);
        fail("삭제된 SKU를 조회하면 예외가 발생해야 합니다");
    } catch (SKUNotFoundException e) {
        assertTrue(e.getMessage().contains(skuId.toString()));
    }
}
```

### 예제 4: 품절 위험 계산 정확성

```java
/**
 * Property: 품절 위험은 재고 비율에 따라 정확히 계산된다
 */
@Property(trials = 100)
public void riskLevelCalculation(
    @InRange(minInt = 0, maxInt = 1000) int currentStock,
    @InRange(minInt = 1, maxInt = 500) int safeStock
) {
    String riskLevel = skuService.calculateRiskLevel(currentStock, safeStock);
    double ratio = (double) currentStock / safeStock;
    
    if (ratio < 0.5) {
        assertEquals("높음", riskLevel);
    } else if (ratio < 1.0) {
        assertEquals("중간", riskLevel);
    } else {
        assertEquals("낮음", riskLevel);
    }
}
```

---

## 문제 해결

### 문제 1: "No tests found" 오류

**증상:**
```
No tests found for given includes: [com.inventory.sku.service.SKUServicePropertyTest]
```

**해결:**
1. JUnit 4와 vintage engine이 의존성에 포함되어 있는지 확인
2. `@RunWith(JUnitQuickcheck.class)` 어노테이션 확인
3. Gradle 캐시 정리: `./gradlew clean`

### 문제 2: Spring 컨텍스트 로드 실패

**증상:**
```
Failed to load ApplicationContext
```

**해결:**
1. `@SpringBootTest` 어노테이션 확인
2. `SpringClassRule`과 `SpringMethodRule` 추가 확인
3. `application-test.yml` 파일 존재 확인
4. H2 데이터베이스 의존성 확인

### 문제 3: 트랜잭션 롤백 안 됨

**증상:**
테스트 간 데이터가 공유되어 중복 오류 발생

**해결:**
1. `@Transactional` 어노테이션 추가
2. 또는 각 테스트에서 명시적으로 cleanup 수행
3. `ddl-auto: create-drop` 설정 확인

### 문제 4: 제너레이터가 유효하지 않은 데이터 생성

**증상:**
```
Validation failed: SKU 코드는 필수입니다
```

**해결:**
1. 제너레이터에서 null이나 빈 문자열 생성하지 않도록 수정
2. 비즈니스 규칙에 맞는 범위 설정
3. 유효성 검증 로직 확인

### 문제 5: 테스트가 너무 느림

**증상:**
100번 반복 테스트가 오래 걸림

**해결:**
1. `trials` 수를 줄임 (개발 중에는 10-20)
2. 테스트 데이터베이스 최적화
3. 불필요한 로깅 비활성화 (`show-sql: false`)
4. 병렬 테스트 실행 설정

```groovy
tasks.named('test') {
    maxParallelForks = Runtime.runtime.availableProcessors().intdiv(2) ?: 1
}
```

---

## 베스트 프랙티스

### 1. 의미 있는 속성 선택

❌ **나쁜 예:**
```java
@Property
public void test(SKURequest request) {
    assertNotNull(skuService.createSKU(request));
}
```

✅ **좋은 예:**
```java
@Property
public void createdSKUCanBeRetrieved(SKURequest request) {
    SKUResponse created = skuService.createSKU(request);
    SKUResponse retrieved = skuService.getSKUById(created.getId());
    assertEquals(created.getSkuCode(), retrieved.getSkuCode());
}
```

### 2. 적절한 trials 수 설정

- **개발 중**: 10-20 trials (빠른 피드백)
- **CI/CD**: 100 trials (표준)
- **릴리스 전**: 1000+ trials (철저한 검증)

### 3. 명확한 실패 메시지

```java
assertEquals("SKU 코드가 일치해야 합니다", 
    expected, actual);
```

### 4. 테스트 격리

각 테스트는 독립적이어야 합니다:
- `@Transactional` 사용
- 또는 명시적 cleanup
- 공유 상태 피하기

### 5. 문서화

각 속성 테스트에 다음을 명시:
- 검증하는 속성
- 관련 요구사항
- 예상 동작

---

## 참고 자료

- [JUnit Quickcheck 공식 문서](https://pholser.github.io/junit-quickcheck/)
- [Property-Based Testing 개념](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Spring Boot Testing 가이드](https://spring.io/guides/gs/testing-web/)

---

## 요약

1. **환경 설정**: Gradle 의존성 + H2 데이터베이스
2. **제너레이터 작성**: 유효한 랜덤 데이터 생성
3. **속성 정의**: 시스템이 만족해야 하는 보편적 규칙
4. **테스트 실행**: `./gradlew test`
5. **결과 확인**: HTML 리포트 또는 콘솔 출력

속성 기반 테스트는 전통적인 단위 테스트를 대체하는 것이 아니라 보완하는 것입니다. 두 가지를 함께 사용하여 포괄적인 테스트 커버리지를 달성하세요!
