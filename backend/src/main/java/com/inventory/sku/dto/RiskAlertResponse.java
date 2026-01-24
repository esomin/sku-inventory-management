package com.inventory.sku.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RiskAlertResponse {

    private Long id;
    private Long skuId;
    private String productName;
    private BigDecimal riskIndex;
    private String alertMessage;
    private LocalDateTime createdAt;
    private Boolean acknowledged;
    private BigDecimal threshold;
    private Map<String, Object> contributingFactors;
}
