package com.inventory.sku.service;

import com.inventory.sku.dto.SKURequest;
import com.inventory.sku.dto.SKUResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.time.LocalDate;

public interface SKUService {

        /**
         * 새로운 SKU를 생성합니다.
         * 
         * @param request SKU 생성 요청 데이터
         * @return 생성된 SKU 응답 데이터
         */
        SKUResponse createSKU(SKURequest request);

        /**
         * ID로 SKU를 조회합니다.
         * 
         * @param id SKU ID
         * @return SKU 응답 데이터
         */
        SKUResponse getSKUById(Long id);

        /**
         * 모든 SKU를 조회합니다 (검색, 필터링, 페이징 지원).
         * 
         * @param searchTerm       검색어
         * @param category         카테고리 필터
         * @param problemStockOnly 문제 재고만 조회 여부
         * @param pageable         페이징 및 정렬 정보
         * @return SKU 페이지
         */
        Page<SKUResponse> getAllSKUs(String searchTerm, String category,
                        Boolean problemStockOnly, Pageable pageable);

        /**
         * SKU를 수정합니다.
         * 
         * @param id      SKU ID
         * @param request SKU 수정 요청 데이터
         * @return 수정된 SKU 응답 데이터
         */
        SKUResponse updateSKU(Long id, SKURequest request);

        /**
         * SKU를 삭제합니다.
         * 
         * @param id SKU ID
         */
        void deleteSKU(Long id);

        /**
         * 품절 위험 수준을 계산합니다.
         * 
         * @param currentStock 현재 재고
         * @param safeStock    안전 재고
         * @return 품절 위험 수준 ("높음", "중간", "낮음")
         */
        String calculateRiskLevel(Integer currentStock, Integer safeStock);

        /**
         * 예상 품절일을 계산합니다.
         * 
         * @param currentStock         현재 재고
         * @param safeStock            안전 재고
         * @param dailyConsumptionRate 일일 소비량
         * @return 예상 품절일
         */
        LocalDate calculateExpectedShortageDate(Integer currentStock, Integer safeStock,
                        Double dailyConsumptionRate);

        /**
         * 칩셋으로 SKU 목록을 조회합니다.
         * 
         * @param chipset  칩셋
         * @param pageable 페이징 및 정렬 정보
         * @return SKU 페이지
         */
        Page<SKUResponse> getSKUsByChipset(String chipset, Pageable pageable);

        /**
         * 브랜드로 SKU 목록을 조회합니다.
         * 
         * @param brand    브랜드
         * @param pageable 페이징 및 정렬 정보
         * @return SKU 페이지
         */
        Page<SKUResponse> getSKUsByBrand(String brand, Pageable pageable);

        /**
         * 여러 SKU를 비교합니다.
         * 
         * @param ids SKU ID 목록
         * @return SKU 응답 목록
         */
        java.util.List<SKUResponse> compareSKUs(java.util.List<Long> ids);

        /**
         * RTX 4070 시리즈 칩셋인지 검증합니다.
         * 
         * @param chipset 칩셋명
         * @return 유효 여부
         */
        boolean isValidRTX4070Chipset(String chipset);

        /**
         * 두 SKU 간 가격 차이를 계산합니다.
         * 
         * @param sku1   첫 번째 SKU
         * @param sku2   두 번째 SKU
         * @param price1 첫 번째 SKU 가격
         * @param price2 두 번째 SKU 가격
         * @return 가격 차이 정보
         */
        com.inventory.sku.dto.SKUComparisonResponse.PriceGap calculatePriceGap(
                        SKUResponse sku1, SKUResponse sku2,
                        java.math.BigDecimal price1, java.math.BigDecimal price2);
}
