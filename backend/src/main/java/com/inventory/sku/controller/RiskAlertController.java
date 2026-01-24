package com.inventory.sku.controller;

import com.inventory.sku.dto.RiskAlertResponse;
import com.inventory.sku.service.RiskAlertService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
@RequestMapping("/api/risk-alerts")
@CrossOrigin(origins = "http://localhost:5173")
@RequiredArgsConstructor
public class RiskAlertController {

    private final RiskAlertService riskAlertService;

    /**
     * 위험 알림을 조회합니다 (필터링, 페이징 지원).
     * 
     * @param acknowledged  확인 여부 (선택)
     * @param skuId         SKU ID (선택)
     * @param startDate     시작 날짜 (선택, ISO 형식: yyyy-MM-dd'T'HH:mm:ss)
     * @param endDate       종료 날짜 (선택, ISO 형식: yyyy-MM-dd'T'HH:mm:ss)
     * @param page          페이지 번호 (0부터 시작)
     * @param size          페이지 크기
     * @param sortBy        정렬 기준 컬럼
     * @param sortDirection 정렬 방향 (ASC/DESC)
     * @return 위험 알림 페이지
     */
    @GetMapping
    public ResponseEntity<Page<RiskAlertResponse>> getRiskAlerts(
            @RequestParam(required = false) Boolean acknowledged,
            @RequestParam(required = false) Long skuId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "DESC") String sortDirection) {

        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<RiskAlertResponse> response = riskAlertService.getRiskAlerts(
                acknowledged, skuId, startDate, endDate, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * 위험 알림을 확인 처리합니다.
     * 
     * @param id 알림 ID
     * @return 업데이트된 위험 알림
     */
    @PutMapping("/{id}/acknowledge")
    public ResponseEntity<RiskAlertResponse> acknowledgeAlert(@PathVariable Long id) {
        RiskAlertResponse response = riskAlertService.acknowledgeAlert(id);
        return ResponseEntity.ok(response);
    }

    /**
     * 확인되지 않은 알림 개수를 조회합니다.
     * 
     * @return 확인되지 않은 알림 개수
     */
    @GetMapping("/unacknowledged/count")
    public ResponseEntity<Map<String, Long>> getUnacknowledgedCount() {
        Long count = riskAlertService.getUnacknowledgedCount();
        return ResponseEntity.ok(Map.of("count", count));
    }
}
