package com.inventory.sku.service;

import com.inventory.sku.dto.RiskAlertResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.time.LocalDateTime;

public interface RiskAlertService {

    /**
     * 위험 알림을 조회합니다 (필터링, 페이징 지원).
     * 
     * @param acknowledged 확인 여부 (선택)
     * @param skuId        SKU ID (선택)
     * @param startDate    시작 날짜 (선택)
     * @param endDate      종료 날짜 (선택)
     * @param pageable     페이징 및 정렬 정보
     * @return 위험 알림 페이지
     */
    Page<RiskAlertResponse> getRiskAlerts(Boolean acknowledged, Long skuId,
            LocalDateTime startDate, LocalDateTime endDate,
            Pageable pageable);

    /**
     * 위험 알림을 확인 처리합니다.
     * 
     * @param id 알림 ID
     * @return 업데이트된 위험 알림
     */
    RiskAlertResponse acknowledgeAlert(Long id);

    /**
     * 확인되지 않은 알림 개수를 조회합니다.
     * 
     * @return 확인되지 않은 알림 개수
     */
    Long getUnacknowledgedCount();
}
