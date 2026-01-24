package com.inventory.sku.service;

import com.inventory.sku.dto.MarketSignalResponse;
import com.inventory.sku.dto.TrendingKeywordResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.time.LocalDate;
import java.util.List;

public interface MarketSignalService {

    /**
     * 커뮤니티 신호를 조회합니다 (필터링, 페이징 지원).
     * 
     * @param keyword   키워드 (선택)
     * @param startDate 시작 날짜 (선택)
     * @param endDate   종료 날짜 (선택)
     * @param pageable  페이징 및 정렬 정보
     * @return 마켓 신호 페이지
     */
    Page<MarketSignalResponse> getMarketSignals(String keyword, LocalDate startDate,
            LocalDate endDate, Pageable pageable);

    /**
     * 트렌딩 키워드를 조회합니다 (전주 대비 50% 이상 증가한 키워드).
     * 
     * @return 트렌딩 키워드 목록
     */
    List<TrendingKeywordResponse> getTrendingKeywords();
}
