package com.inventory.sku.service;

import com.inventory.sku.dto.PriceLogResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.time.LocalDateTime;
import java.util.List;

public interface PriceLogService {

    /**
     * 가격 로그를 조회합니다 (필터링, 페이징 지원).
     * 
     * @param skuId     SKU ID (선택)
     * @param startDate 시작 날짜 (선택)
     * @param endDate   종료 날짜 (선택)
     * @param pageable  페이징 및 정렬 정보
     * @return 가격 로그 페이지
     */
    Page<PriceLogResponse> getPriceLogs(Long skuId, LocalDateTime startDate,
            LocalDateTime endDate, Pageable pageable);

    /**
     * SKU ID로 최신 가격을 조회합니다.
     * 
     * @param skuId SKU ID
     * @return 최신 가격 로그
     */
    PriceLogResponse getLatestPriceBySkuId(Long skuId);

    /**
     * 모든 SKU의 최신 가격을 조회합니다.
     * 
     * @return 최신 가격 로그 목록
     */
    List<PriceLogResponse> getAllLatestPrices();
}
