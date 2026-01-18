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
import org.springframework.test.context.junit4.rules.SpringClassRule;
import org.springframework.test.context.junit4.rules.SpringMethodRule;
import org.springframework.transaction.annotation.Transactional;

import org.springframework.test.context.ActiveProfiles;

import static org.junit.Assert.*;

import org.junit.ClassRule;
import org.junit.Rule;

/**
 * Property-based tests for SKU CRUD operations.
 * Feature: sku-inventory-management
 * 
 * Tests the following properties:
 * - Property 1: SKU 생성 라운드트립
 * - Property 5: SKU 업데이트 라운드트립
 * - Property 6: SKU 삭제 효과
 * 
 * Validates: Requirements 1.1, 1.4, 2.3, 3.1, 3.4, 4.1, 4.3
 */
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
         * 동일한 데이터(ID 제외)를 반환해야 한다.
         * 
         * Validates: Requirements 1.1, 1.4, 2.3
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
                assertNotNull("조회된 SKU는 null이 아니어야 합니다", retrieved);

                assertEquals("SKU 코드가 일치해야 합니다",
                                request.getSkuCode(), retrieved.getSkuCode());
                assertEquals("제품명이 일치해야 합니다",
                                request.getProductName(), retrieved.getProductName());
                assertEquals("카테고리가 일치해야 합니다",
                                request.getCategory(), retrieved.getCategory());
                assertEquals("현재 재고가 일치해야 합니다",
                                request.getCurrentStock(), retrieved.getCurrentStock());
                assertEquals("안전 재고가 일치해야 합니다",
                                request.getSafeStock(), retrieved.getSafeStock());

                // 계산된 필드도 존재해야 함
                assertNotNull("품절 위험이 계산되어야 합니다", retrieved.getRiskLevel());
                assertNotNull("생성 시간이 설정되어야 합니다", retrieved.getCreatedAt());
                assertNotNull("수정 시간이 설정되어야 합니다", retrieved.getUpdatedAt());

                // Cleanup: 테스트 데이터 삭제
                skuService.deleteSKU(created.getId());
        }

        /**
         * Property 5: SKU 업데이트 라운드트립
         * 
         * 모든 유효한 SKU 업데이트 요청에 대해, SKU를 업데이트한 후 조회하면
         * 업데이트된 데이터가 반환되어야 한다.
         * 
         * Validates: Requirements 3.1, 3.4
         */
        @Property(trials = 100)
        public void skuUpdateRoundTrip(
                        @From(SKURequestGenerator.class) SKURequest initialRequest,
                        @From(SKURequestGenerator.class) SKURequest updateRequest) {
                // Given: 생성된 SKU
                SKUResponse created = skuService.createSKU(initialRequest);
                Long skuId = created.getId();

                // When: SKU를 업데이트하고 조회
                // Note: SKU 코드는 동일하게 유지 (중복 방지)
                updateRequest.setSkuCode(initialRequest.getSkuCode());

                SKUResponse updated = skuService.updateSKU(skuId, updateRequest);
                SKUResponse retrieved = skuService.getSKUById(skuId);

                // Then: 업데이트된 데이터와 조회된 데이터가 일치해야 함
                assertNotNull("업데이트된 SKU는 null이 아니어야 합니다", updated);
                assertNotNull("조회된 SKU는 null이 아니어야 합니다", retrieved);
                assertEquals("ID가 동일해야 합니다", skuId, retrieved.getId());

                assertEquals("업데이트된 SKU 코드가 일치해야 합니다",
                                updateRequest.getSkuCode(), retrieved.getSkuCode());
                assertEquals("업데이트된 제품명이 일치해야 합니다",
                                updateRequest.getProductName(), retrieved.getProductName());
                assertEquals("업데이트된 카테고리가 일치해야 합니다",
                                updateRequest.getCategory(), retrieved.getCategory());
                assertEquals("업데이트된 현재 재고가 일치해야 합니다",
                                updateRequest.getCurrentStock(), retrieved.getCurrentStock());
                assertEquals("업데이트된 안전 재고가 일치해야 합니다",
                                updateRequest.getSafeStock(), retrieved.getSafeStock());

                // 수정 시간이 업데이트되어야 함
                assertNotNull("수정 시간이 업데이트되어야 합니다", retrieved.getUpdatedAt());

                // Cleanup: 테스트 데이터 삭제
                skuService.deleteSKU(skuId);
        }

        /**
         * Property 6: SKU 삭제 효과
         * 
         * 모든 유효한 SKU ID에 대해, SKU를 삭제한 후 해당 ID로 조회하면
         * SKUNotFoundException이 발생해야 한다.
         * 
         * Validates: Requirements 4.1, 4.3
         */
        @Property(trials = 100)
        public void skuDeletionEffect(@From(SKURequestGenerator.class) SKURequest request) {
                // Given: 생성된 SKU
                SKUResponse created = skuService.createSKU(request);
                Long skuId = created.getId();

                // 삭제 전에는 조회 가능해야 함
                SKUResponse beforeDelete = skuService.getSKUById(skuId);
                assertNotNull("삭제 전에는 SKU를 조회할 수 있어야 합니다", beforeDelete);

                // When: SKU를 삭제
                skuService.deleteSKU(skuId);

                // Then: 삭제 후 조회 시 SKUNotFoundException이 발생해야 함
                try {
                        skuService.getSKUById(skuId);
                        fail("삭제된 SKU를 조회하면 SKUNotFoundException이 발생해야 합니다");
                } catch (SKUNotFoundException e) {
                        // Expected exception
                        assertTrue("예외 메시지에 ID가 포함되어야 합니다",
                                        e.getMessage().contains(skuId.toString()));
                }

                // 동일한 ID로 다시 삭제 시도 시에도 예외가 발생해야 함
                try {
                        skuService.deleteSKU(skuId);
                        fail("존재하지 않는 SKU를 삭제하면 SKUNotFoundException이 발생해야 합니다");
                } catch (SKUNotFoundException e) {
                        // Expected exception
                }
        }
}
