package com.inventory.sku.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PriceLogResponse {

    private Long id;
    private Long skuId;
    private String productName;
    private BigDecimal price;
    private LocalDateTime recordedAt;
    private String sourceUrl;
    private String sourceName;
    private BigDecimal priceChangePct;
    private LocalDateTime createdAt;
}
