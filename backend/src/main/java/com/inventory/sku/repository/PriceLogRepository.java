package com.inventory.sku.repository;

import com.inventory.sku.entity.PriceLog;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface PriceLogRepository extends JpaRepository<PriceLog, Long> {

    /**
     * SKU ID로 가격 로그를 조회합니다.
     */
    Page<PriceLog> findBySkuId(Long skuId, Pageable pageable);

    /**
     * SKU ID와 날짜 범위로 가격 로그를 조회합니다.
     */
    @Query("SELECT p FROM PriceLog p WHERE p.skuId = :skuId " +
            "AND p.recordedAt BETWEEN :startDate AND :endDate " +
            "ORDER BY p.recordedAt DESC")
    Page<PriceLog> findBySkuIdAndDateRange(
            @Param("skuId") Long skuId,
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate,
            Pageable pageable);

    /**
     * 날짜 범위로 가격 로그를 조회합니다.
     */
    @Query("SELECT p FROM PriceLog p WHERE p.recordedAt BETWEEN :startDate AND :endDate " +
            "ORDER BY p.recordedAt DESC")
    Page<PriceLog> findByDateRange(
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate,
            Pageable pageable);

    /**
     * SKU ID로 최신 가격 로그를 조회합니다.
     */
    @Query("SELECT p FROM PriceLog p WHERE p.skuId = :skuId " +
            "ORDER BY p.recordedAt DESC LIMIT 1")
    Optional<PriceLog> findLatestBySkuId(@Param("skuId") Long skuId);

    /**
     * 모든 SKU의 최신 가격 로그를 조회합니다.
     */
    @Query("SELECT p FROM PriceLog p WHERE p.id IN " +
            "(SELECT MAX(p2.id) FROM PriceLog p2 GROUP BY p2.skuId) " +
            "ORDER BY p.recordedAt DESC")
    List<PriceLog> findAllLatest();
}
