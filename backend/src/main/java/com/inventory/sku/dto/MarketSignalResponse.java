package com.inventory.sku.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MarketSignalResponse {

    private Long id;
    private String keyword;
    private BigDecimal sentimentScore;
    private Integer mentionCount;
    private LocalDate date;
    private String postTitle;
    private String postUrl;
    private String subreddit;
    private LocalDateTime createdAt;
}
