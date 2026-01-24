package com.inventory.sku.repository;

import com.inventory.sku.entity.RiskAlert;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;

@Repository
public interface RiskAlertRepository extends JpaRepository<RiskAlert, Long> {

    /**
     * 확인 여부로 위험 알림을 조회합니다.
     */
    Page<RiskAlert> findByAcknowledged(Boolean acknowledged, Pageable pageable);

    /**
     * SKU ID로 위험 알림을 조회합니다.
     */
    Page<RiskAlert> findBySkuId(Long skuId, Pageable pageable);

    /**
     * SKU ID와 확인 여부로 위험 알림을 조회합니다.
     */
    Page<RiskAlert> findBySkuIdAndAcknowledged(Long skuId, Boolean acknowledged, Pageable pageable);

    /**
     * 날짜 범위로 위험 알림을 조회합니다.
     */
    @Query("SELECT r FROM RiskAlert r WHERE r.createdAt BETWEEN :startDate AND :endDate " +
            "ORDER BY r.createdAt DESC")
    Page<RiskAlert> findByDateRange(
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate,
            Pageable pageable);

    /**
     * 확인되지 않은 알림 개수를 조회합니다.
     */
    @Query("SELECT COUNT(r) FROM RiskAlert r WHERE r.acknowledged = false")
    Long countUnacknowledged();
}
