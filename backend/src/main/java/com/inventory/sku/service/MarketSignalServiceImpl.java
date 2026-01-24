package com.inventory.sku.service;

import com.inventory.sku.dto.MarketSignalResponse;
import com.inventory.sku.dto.TrendingKeywordResponse;
import com.inventory.sku.entity.MarketSignal;
import com.inventory.sku.repository.MarketSignalRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MarketSignalServiceImpl implements MarketSignalService {

    private final MarketSignalRepository marketSignalRepository;

    @Override
    public Page<MarketSignalResponse> getMarketSignals(String keyword, LocalDate startDate,
            LocalDate endDate, Pageable pageable) {
        Page<MarketSignal> marketSignals;

        if (keyword != null && startDate != null && endDate != null) {
            // 키워드와 날짜 범위로 필터링
            marketSignals = marketSignalRepository.findByKeywordAndDateRange(
                    keyword, startDate, endDate, pageable);
        } else if (keyword != null) {
            // 키워드로만 필터링
            marketSignals = marketSignalRepository.findByKeyword(keyword, pageable);
        } else if (startDate != null && endDate != null) {
            // 날짜 범위로만 필터링
            marketSignals = marketSignalRepository.findByDateRange(startDate, endDate, pageable);
        } else {
            // 필터 없이 전체 조회
            marketSignals = marketSignalRepository.findAll(pageable);
        }

        return marketSignals.map(this::convertToResponse);
    }

    @Override
    public List<TrendingKeywordResponse> getTrendingKeywords() {
        LocalDate today = LocalDate.now();
        LocalDate oneWeekAgo = today.minusWeeks(1);
        LocalDate twoWeeksAgo = today.minusWeeks(2);

        // 현재 주 (지난 7일) 키워드별 언급 횟수
        List<Object[]> currentWeekData = marketSignalRepository
                .countMentionsByKeywordAndDateRange(oneWeekAgo, today);

        List<TrendingKeywordResponse> trendingKeywords = new ArrayList<>();

        for (Object[] row : currentWeekData) {
            String keyword = (String) row[0];
            Long currentWeekMentionsLong = (Long) row[1];
            Integer currentWeekMentions = currentWeekMentionsLong != null
                    ? currentWeekMentionsLong.intValue()
                    : 0;

            // 이전 주 (7-14일 전) 언급 횟수
            Integer lastWeekMentions = marketSignalRepository
                    .sumMentionCountByKeywordAndDateRange(keyword, twoWeeksAgo, oneWeekAgo);

            if (lastWeekMentions == null) {
                lastWeekMentions = 0;
            }

            // 성장률 계산
            BigDecimal growthPercentage = BigDecimal.ZERO;
            if (lastWeekMentions > 0) {
                growthPercentage = BigDecimal.valueOf(currentWeekMentions - lastWeekMentions)
                        .multiply(BigDecimal.valueOf(100))
                        .divide(BigDecimal.valueOf(lastWeekMentions), 2, RoundingMode.HALF_UP);
            } else if (currentWeekMentions > 0) {
                // 이전 주에 언급이 없었다면 무한대 성장으로 간주 (100%로 표시)
                growthPercentage = BigDecimal.valueOf(100);
            }

            // 50% 이상 증가한 경우 트렌딩으로 표시
            boolean isTrending = growthPercentage.compareTo(BigDecimal.valueOf(50)) > 0;

            TrendingKeywordResponse response = new TrendingKeywordResponse();
            response.setKeyword(keyword);
            response.setCurrentWeekMentions(currentWeekMentions);
            response.setLastWeekMentions(lastWeekMentions);
            response.setGrowthPercentage(growthPercentage);
            response.setIsTrending(isTrending);

            trendingKeywords.add(response);
        }

        // 성장률 기준으로 정렬 (내림차순)
        return trendingKeywords.stream()
                .sorted((a, b) -> b.getGrowthPercentage().compareTo(a.getGrowthPercentage()))
                .collect(Collectors.toList());
    }

    private MarketSignalResponse convertToResponse(MarketSignal marketSignal) {
        MarketSignalResponse response = new MarketSignalResponse();
        response.setId(marketSignal.getId());
        response.setKeyword(marketSignal.getKeyword());
        response.setSentimentScore(marketSignal.getSentimentScore());
        response.setMentionCount(marketSignal.getMentionCount());
        response.setDate(marketSignal.getDate());
        response.setPostTitle(marketSignal.getPostTitle());
        response.setPostUrl(marketSignal.getPostUrl());
        response.setSubreddit(marketSignal.getSubreddit());
        response.setCreatedAt(marketSignal.getCreatedAt());
        return response;
    }
}
