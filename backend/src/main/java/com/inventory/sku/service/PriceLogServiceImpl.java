package com.inventory.sku.service;

import com.inventory.sku.dto.PriceLogResponse;
import com.inventory.sku.entity.PriceLog;
import com.inventory.sku.entity.SKU;
import com.inventory.sku.exception.SKUNotFoundException;
import com.inventory.sku.repository.PriceLogRepository;
import com.inventory.sku.repository.SKURepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PriceLogServiceImpl implements PriceLogService {

    private final PriceLogRepository priceLogRepository;
    private final SKURepository skuRepository;

    @Override
    public Page<PriceLogResponse> getPriceLogs(Long skuId, LocalDateTime startDate,
            LocalDateTime endDate, Pageable pageable) {
        Page<PriceLog> priceLogs;

        if (skuId != null && startDate != null && endDate != null) {
            // SKU ID와 날짜 범위로 필터링
            priceLogs = priceLogRepository.findBySkuIdAndDateRange(skuId, startDate, endDate, pageable);
        } else if (skuId != null) {
            // SKU ID로만 필터링
            priceLogs = priceLogRepository.findBySkuId(skuId, pageable);
        } else if (startDate != null && endDate != null) {
            // 날짜 범위로만 필터링
            priceLogs = priceLogRepository.findByDateRange(startDate, endDate, pageable);
        } else {
            // 필터 없이 전체 조회
            priceLogs = priceLogRepository.findAll(pageable);
        }

        return priceLogs.map(this::convertToResponse);
    }

    @Override
    public PriceLogResponse getLatestPriceBySkuId(Long skuId) {
        // SKU 존재 여부 확인
        SKU sku = skuRepository.findById(skuId)
                .orElseThrow(() -> new SKUNotFoundException("SKU를 찾을 수 없습니다: " + skuId));

        PriceLog priceLog = priceLogRepository.findLatestBySkuId(skuId)
                .orElseThrow(() -> new SKUNotFoundException(
                        "SKU ID " + skuId + "에 대한 가격 로그를 찾을 수 없습니다"));

        return convertToResponse(priceLog, sku.getProductName());
    }

    @Override
    public List<PriceLogResponse> getAllLatestPrices() {
        List<PriceLog> latestPriceLogs = priceLogRepository.findAllLatest();
        return latestPriceLogs.stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    private PriceLogResponse convertToResponse(PriceLog priceLog) {
        SKU sku = skuRepository.findById(priceLog.getSkuId()).orElse(null);
        String productName = sku != null ? sku.getProductName() : null;
        return convertToResponse(priceLog, productName);
    }

    private PriceLogResponse convertToResponse(PriceLog priceLog, String productName) {
        PriceLogResponse response = new PriceLogResponse();
        response.setId(priceLog.getId());
        response.setSkuId(priceLog.getSkuId());
        response.setProductName(productName);
        response.setPrice(priceLog.getPrice());
        response.setRecordedAt(priceLog.getRecordedAt());
        response.setSourceUrl(priceLog.getSourceUrl());
        response.setSourceName(priceLog.getSourceName());
        response.setPriceChangePct(priceLog.getPriceChangePct());
        response.setCreatedAt(priceLog.getCreatedAt());
        return response;
    }
}
