package com.inventory.sku.controller;

import com.inventory.sku.dto.PriceLogResponse;
import com.inventory.sku.service.PriceLogService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/price-logs")
@CrossOrigin(origins = "http://localhost:5173")
@RequiredArgsConstructor
public class PriceLogController {

    private final PriceLogService priceLogService;

    /**
     * 가격 로그를 조회합니다 (필터링, 페이징 지원).
     * 
     * @param skuId         SKU ID (선택)
     * @param startDate     시작 날짜 (선택, ISO 형식: yyyy-MM-dd'T'HH:mm:ss)
     * @param endDate       종료 날짜 (선택, ISO 형식: yyyy-MM-dd'T'HH:mm:ss)
     * @param page          페이지 번호 (0부터 시작)
     * @param size          페이지 크기
     * @param sortBy        정렬 기준 컬럼
     * @param sortDirection 정렬 방향 (ASC/DESC)
     * @return 가격 로그 페이지
     */
    @GetMapping
    public ResponseEntity<Page<PriceLogResponse>> getPriceLogs(
            @RequestParam(required = false) Long skuId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "recordedAt") String sortBy,
            @RequestParam(defaultValue = "DESC") String sortDirection) {

        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<PriceLogResponse> response = priceLogService.getPriceLogs(
                skuId, startDate, endDate, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * SKU ID로 최신 가격을 조회합니다.
     * 
     * @param skuId SKU ID
     * @return 최신 가격 로그
     */
    @GetMapping("/latest")
    public ResponseEntity<PriceLogResponse> getLatestPrice(
            @RequestParam Long skuId) {
        PriceLogResponse response = priceLogService.getLatestPriceBySkuId(skuId);
        return ResponseEntity.ok(response);
    }

    /**
     * 모든 SKU의 최신 가격을 조회합니다.
     * 
     * @return 최신 가격 로그 목록
     */
    @GetMapping("/latest/all")
    public ResponseEntity<List<PriceLogResponse>> getAllLatestPrices() {
        List<PriceLogResponse> response = priceLogService.getAllLatestPrices();
        return ResponseEntity.ok(response);
    }
}
