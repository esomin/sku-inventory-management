package com.inventory.sku.repository;

import com.inventory.sku.entity.MarketSignal;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface MarketSignalRepository extends JpaRepository<MarketSignal, Long> {

    /**
     * 날짜 범위로 마켓 신호를 조회합니다.
     */
    @Query("SELECT m FROM MarketSignal m WHERE m.date BETWEEN :startDate AND :endDate " +
            "ORDER BY m.date DESC")
    Page<MarketSignal> findByDateRange(
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate,
            Pageable pageable);

    /**
     * 키워드로 마켓 신호를 조회합니다.
     */
    Page<MarketSignal> findByKeyword(String keyword, Pageable pageable);

    /**
     * 키워드와 날짜 범위로 마켓 신호를 조회합니다.
     */
    @Query("SELECT m FROM MarketSignal m WHERE m.keyword = :keyword " +
            "AND m.date BETWEEN :startDate AND :endDate " +
            "ORDER BY m.date DESC")
    Page<MarketSignal> findByKeywordAndDateRange(
            @Param("keyword") String keyword,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate,
            Pageable pageable);

    /**
     * 날짜 범위 내 키워드별 언급 횟수를 집계합니다.
     */
    @Query("SELECT m.keyword, SUM(m.mentionCount) FROM MarketSignal m " +
            "WHERE m.date BETWEEN :startDate AND :endDate " +
            "GROUP BY m.keyword " +
            "ORDER BY SUM(m.mentionCount) DESC")
    List<Object[]> countMentionsByKeywordAndDateRange(
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);

    /**
     * 특정 날짜 범위 내 키워드의 총 언급 횟수를 조회합니다.
     */
    @Query("SELECT SUM(m.mentionCount) FROM MarketSignal m " +
            "WHERE m.keyword = :keyword AND m.date BETWEEN :startDate AND :endDate")
    Integer sumMentionCountByKeywordAndDateRange(
            @Param("keyword") String keyword,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);
}
