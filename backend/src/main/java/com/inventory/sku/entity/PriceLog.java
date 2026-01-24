package com.inventory.sku.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "price_logs")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PriceLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "sku_id", nullable = false)
    @NotNull(message = "SKU ID는 필수입니다")
    private Long skuId;

    @Column(nullable = false, precision = 10, scale = 2)
    @NotNull(message = "가격은 필수입니다")
    private BigDecimal price;

    @Column(name = "recorded_at", nullable = false)
    @NotNull(message = "기록 시간은 필수입니다")
    private LocalDateTime recordedAt;

    @Column(name = "source_url", length = 500)
    private String sourceUrl;

    @Column(name = "source_name", nullable = false, length = 50)
    @NotNull(message = "소스명은 필수입니다")
    private String sourceName = "다나와";

    @Column(name = "price_change_pct", precision = 5, scale = 2)
    private BigDecimal priceChangePct;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
