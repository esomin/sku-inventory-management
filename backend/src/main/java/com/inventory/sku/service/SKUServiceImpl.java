package com.inventory.sku.service;

import com.inventory.sku.dto.SKURequest;
import com.inventory.sku.dto.SKUResponse;
import com.inventory.sku.entity.SKU;
import com.inventory.sku.exception.DuplicateSKUException;
import com.inventory.sku.exception.SKUNotFoundException;
import com.inventory.sku.repository.SKURepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Service
@Transactional
@RequiredArgsConstructor
public class SKUServiceImpl implements SKUService {

    private final SKURepository skuRepository;

    @Override
    public SKUResponse createSKU(SKURequest request) {
        // 중복 체크
        if (skuRepository.existsBySkuCode(request.getSkuCode())) {
            throw new DuplicateSKUException("SKU 코드가 이미 존재합니다: " + request.getSkuCode());
        }

        // RTX 4070 시리즈 칩셋 검증
        if (request.getChipset() != null && !request.getChipset().isEmpty()) {
            if (!isValidRTX4070Chipset(request.getChipset())) {
                throw new IllegalArgumentException(
                        "chipset은 RTX 4070 시리즈만 허용됩니다: RTX 4070, RTX 4070 Super, RTX 4070 Ti, RTX 4070 Ti Super");
            }
        }

        SKU sku = mapToEntity(request);
        sku.setCreatedAt(LocalDateTime.now());
        sku.setUpdatedAt(LocalDateTime.now());

        SKU savedSKU = skuRepository.save(sku);
        return mapToResponse(savedSKU);
    }

    @Override
    @Transactional(readOnly = true)
    public SKUResponse getSKUById(Long id) {
        SKU sku = skuRepository.findById(id)
                .orElseThrow(() -> new SKUNotFoundException(id));
        return mapToResponse(sku);
    }

    @Override
    @Transactional(readOnly = true)
    public Page<SKUResponse> getAllSKUs(String searchTerm, String category,
            Boolean problemStockOnly, Pageable pageable) {
        Page<SKU> skuPage = skuRepository.findWithFilters(
                searchTerm, category, problemStockOnly, pageable);
        return skuPage.map(this::mapToResponse);
    }

    @Override
    public SKUResponse updateSKU(Long id, SKURequest request) {
        SKU sku = skuRepository.findById(id)
                .orElseThrow(() -> new SKUNotFoundException(id));

        // SKU 코드 변경 시 중복 체크
        if (!sku.getSkuCode().equals(request.getSkuCode()) &&
                skuRepository.existsBySkuCode(request.getSkuCode())) {
            throw new DuplicateSKUException("SKU 코드가 이미 존재합니다: " + request.getSkuCode());
        }

        // RTX 4070 시리즈 칩셋 검증
        if (request.getChipset() != null && !request.getChipset().isEmpty()) {
            if (!isValidRTX4070Chipset(request.getChipset())) {
                throw new IllegalArgumentException(
                        "chipset은 RTX 4070 시리즈만 허용됩니다: RTX 4070, RTX 4070 Super, RTX 4070 Ti, RTX 4070 Ti Super");
            }
        }

        updateEntityFromRequest(sku, request);
        sku.setUpdatedAt(LocalDateTime.now());

        SKU updatedSKU = skuRepository.save(sku);
        return mapToResponse(updatedSKU);
    }

    @Override
    public void deleteSKU(Long id) {
        if (!skuRepository.existsById(id)) {
            throw new SKUNotFoundException(id);
        }
        skuRepository.deleteById(id);
    }

    @Override
    public String calculateRiskLevel(Integer currentStock, Integer safeStock) {
        if (safeStock == 0) {
            return "낮음";
        }

        double ratio = (double) currentStock / safeStock;

        if (ratio < 0.5) {
            return "높음";
        } else if (ratio < 1.0) {
            return "중간";
        } else {
            return "낮음";
        }
    }

    @Override
    public LocalDate calculateExpectedShortageDate(Integer currentStock, Integer safeStock,
            Double dailyConsumptionRate) {
        if (currentStock <= safeStock) {
            return LocalDate.now(); // 즉시
        }

        if (dailyConsumptionRate <= 0) {
            return null; // 소비가 없으면 품절 없음
        }

        // 간단한 선형 계산: (현재재고 - 안전재고) / 일일소비량
        int daysUntilShortage = (int) Math.ceil((currentStock - safeStock) / dailyConsumptionRate);
        return LocalDate.now().plusDays(daysUntilShortage);
    }

    private SKU mapToEntity(SKURequest request) {
        SKU sku = new SKU();
        sku.setSkuCode(request.getSkuCode());
        sku.setProductName(request.getProductName());
        sku.setCategory(request.getCategory());
        sku.setCurrentStock(request.getCurrentStock());
        sku.setSafeStock(request.getSafeStock());
        sku.setDailyConsumptionRate(request.getDailyConsumptionRate());

        // GPU 특화 필드 매핑
        sku.setChipset(request.getChipset());
        sku.setBrand(request.getBrand());
        sku.setModelName(request.getModelName());
        sku.setVram(request.getVram());
        sku.setIsOc(request.getIsOc());

        return sku;
    }

    private void updateEntityFromRequest(SKU sku, SKURequest request) {
        sku.setSkuCode(request.getSkuCode());
        sku.setProductName(request.getProductName());
        sku.setCategory(request.getCategory());
        sku.setCurrentStock(request.getCurrentStock());
        sku.setSafeStock(request.getSafeStock());
        sku.setDailyConsumptionRate(request.getDailyConsumptionRate());

        // GPU 특화 필드 업데이트
        sku.setChipset(request.getChipset());
        sku.setBrand(request.getBrand());
        sku.setModelName(request.getModelName());
        sku.setVram(request.getVram());
        sku.setIsOc(request.getIsOc());
    }

    private SKUResponse mapToResponse(SKU sku) {
        SKUResponse response = new SKUResponse();
        response.setId(sku.getId());
        response.setSkuCode(sku.getSkuCode());
        response.setProductName(sku.getProductName());
        response.setCategory(sku.getCategory());
        response.setCurrentStock(sku.getCurrentStock());
        response.setSafeStock(sku.getSafeStock());
        response.setCreatedAt(sku.getCreatedAt());
        response.setUpdatedAt(sku.getUpdatedAt());

        // GPU 특화 필드 매핑
        response.setChipset(sku.getChipset());
        response.setBrand(sku.getBrand());
        response.setModelName(sku.getModelName());
        response.setVram(sku.getVram());
        response.setIsOc(sku.getIsOc());

        // 계산된 필드
        response.setRiskLevel(calculateRiskLevel(sku.getCurrentStock(), sku.getSafeStock()));
        response.setExpectedShortageDate(calculateExpectedShortageDate(
                sku.getCurrentStock(), sku.getSafeStock(), sku.getDailyConsumptionRate()));

        return response;
    }

    @Override
    @Transactional(readOnly = true)
    public Page<SKUResponse> getSKUsByChipset(String chipset, Pageable pageable) {
        Page<SKU> skuPage = skuRepository.findByChipset(chipset, pageable);
        return skuPage.map(this::mapToResponse);
    }

    @Override
    @Transactional(readOnly = true)
    public Page<SKUResponse> getSKUsByBrand(String brand, Pageable pageable) {
        Page<SKU> skuPage = skuRepository.findByBrand(brand, pageable);
        return skuPage.map(this::mapToResponse);
    }

    @Override
    @Transactional(readOnly = true)
    public java.util.List<SKUResponse> compareSKUs(java.util.List<Long> ids) {
        java.util.List<SKU> skus = skuRepository.findAllById(ids);
        return skus.stream()
                .map(this::mapToResponse)
                .collect(java.util.stream.Collectors.toList());
    }

    @Override
    public boolean isValidRTX4070Chipset(String chipset) {
        if (chipset == null || chipset.isEmpty()) {
            return false;
        }

        java.util.List<String> validChipsets = java.util.Arrays.asList(
                "RTX 4070",
                "RTX 4070 Super",
                "RTX 4070 Ti",
                "RTX 4070 Ti Super");

        return validChipsets.contains(chipset);
    }

    @Override
    public com.inventory.sku.dto.SKUComparisonResponse.PriceGap calculatePriceGap(
            SKUResponse sku1, SKUResponse sku2,
            java.math.BigDecimal price1, java.math.BigDecimal price2) {

        if (price1 == null || price2 == null) {
            throw new IllegalArgumentException("가격 정보가 없습니다");
        }

        java.math.BigDecimal gap = price1.subtract(price2).abs();
        String comparison;

        if (price1.compareTo(price2) > 0) {
            comparison = String.format("%s이(가) %s보다 %s원 비쌈",
                    sku1.getProductName(), sku2.getProductName(), gap.toString());
        } else if (price1.compareTo(price2) < 0) {
            comparison = String.format("%s이(가) %s보다 %s원 저렴",
                    sku1.getProductName(), sku2.getProductName(), gap.toString());
        } else {
            comparison = String.format("%s과(와) %s의 가격이 동일",
                    sku1.getProductName(), sku2.getProductName());
        }

        com.inventory.sku.dto.SKUComparisonResponse.PriceGap priceGap = new com.inventory.sku.dto.SKUComparisonResponse.PriceGap();
        priceGap.setSku1Id(sku1.getId());
        priceGap.setSku2Id(sku2.getId());
        priceGap.setSku1Name(sku1.getProductName());
        priceGap.setSku2Name(sku2.getProductName());
        priceGap.setPriceGap(gap);
        priceGap.setComparison(comparison);

        return priceGap;
    }
}
