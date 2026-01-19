package com.inventory.sku.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SKUComparisonResponse {

    private List<SKUResponse> skus;
    private List<PriceGap> priceGaps;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PriceGap {
        private Long sku1Id;
        private Long sku2Id;
        private String sku1Name;
        private String sku2Name;
        private BigDecimal priceGap;
        private String comparison; // "SKU1이 SKU2보다 X원 비쌈" 또는 "SKU1이 SKU2보다 X원 저렴"
    }
}
