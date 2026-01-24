package com.inventory.sku.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "risk_alerts")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RiskAlert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "sku_id", nullable = false)
    @NotNull(message = "SKU ID는 필수입니다")
    private Long skuId;

    @Column(name = "risk_index", nullable = false, precision = 10, scale = 2)
    @NotNull(message = "위험 지수는 필수입니다")
    private BigDecimal riskIndex;

    @Column(name = "alert_message", nullable = false, columnDefinition = "TEXT")
    @NotBlank(message = "알림 메시지는 필수입니다")
    private String alertMessage;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private Boolean acknowledged = false;

    @Column(precision = 10, scale = 2)
    private BigDecimal threshold;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "contributing_factors", columnDefinition = "jsonb")
    private Map<String, Object> contributingFactors;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (acknowledged == null) {
            acknowledged = false;
        }
    }
}
