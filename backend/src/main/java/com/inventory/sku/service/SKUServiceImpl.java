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
        return sku;
    }
    
    private void updateEntityFromRequest(SKU sku, SKURequest request) {
        sku.setSkuCode(request.getSkuCode());
        sku.setProductName(request.getProductName());
        sku.setCategory(request.getCategory());
        sku.setCurrentStock(request.getCurrentStock());
        sku.setSafeStock(request.getSafeStock());
        sku.setDailyConsumptionRate(request.getDailyConsumptionRate());
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
        
        // 계산된 필드
        response.setRiskLevel(calculateRiskLevel(sku.getCurrentStock(), sku.getSafeStock()));
        response.setExpectedShortageDate(calculateExpectedShortageDate(
            sku.getCurrentStock(), sku.getSafeStock(), sku.getDailyConsumptionRate()));
        
        return response;
    }
}
