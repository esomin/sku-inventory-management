package com.inventory.sku.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SKUResponse {

    private Long id;
    private String skuCode;
    private String productName;
    private String category;
    private Integer currentStock;
    private Integer safeStock;
    private String riskLevel; // "높음", "중간", "낮음"
    private LocalDate expectedShortageDate; // 예상 품절일
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    // GPU 특화 필드
    private String chipset;
    private String brand;
    private String modelName;
    private String vram;
    private Boolean isOc;
}
