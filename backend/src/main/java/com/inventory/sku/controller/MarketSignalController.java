package com.inventory.sku.controller;

import com.inventory.sku.dto.MarketSignalResponse;
import com.inventory.sku.dto.TrendingKeywordResponse;
import com.inventory.sku.service.MarketSignalService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/market-signals")
@CrossOrigin(origins = "http://localhost:5173")
@RequiredArgsConstructor
public class MarketSignalController {

    private final MarketSignalService marketSignalService;

    /**
     * 커뮤니티 신호를 조회합니다 (필터링, 페이징 지원).
     * 
     * @param keyword       키워드 (선택)
     * @param startDate     시작 날짜 (선택, ISO 형식: yyyy-MM-dd)
     * @param endDate       종료 날짜 (선택, ISO 형식: yyyy-MM-dd)
     * @param page          페이지 번호 (0부터 시작)
     * @param size          페이지 크기
     * @param sortBy        정렬 기준 컬럼
     * @param sortDirection 정렬 방향 (ASC/DESC)
     * @return 마켓 신호 페이지
     */
    @GetMapping
    public ResponseEntity<Page<MarketSignalResponse>> getMarketSignals(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "date") String sortBy,
            @RequestParam(defaultValue = "DESC") String sortDirection) {

        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<MarketSignalResponse> response = marketSignalService.getMarketSignals(
                keyword, startDate, endDate, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * 트렌딩 키워드를 조회합니다 (전주 대비 50% 이상 증가한 키워드).
     * 
     * @return 트렌딩 키워드 목록
     */
    @GetMapping("/trending")
    public ResponseEntity<List<TrendingKeywordResponse>> getTrendingKeywords() {
        List<TrendingKeywordResponse> response = marketSignalService.getTrendingKeywords();
        return ResponseEntity.ok(response);
    }
}
