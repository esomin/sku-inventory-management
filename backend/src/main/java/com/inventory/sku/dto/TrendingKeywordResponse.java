package com.inventory.sku.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrendingKeywordResponse {

    private String keyword;
    private Integer currentWeekMentions;
    private Integer lastWeekMentions;
    private BigDecimal growthPercentage;
    private Boolean isTrending; // true if growth > 50%
}
