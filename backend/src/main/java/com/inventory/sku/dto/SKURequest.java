package com.inventory.sku.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SKURequest {

    @NotBlank(message = "SKU 코드는 필수입니다")
    private String skuCode;

    @NotBlank(message = "제품명은 필수입니다")
    private String productName;

    @NotBlank(message = "카테고리는 필수입니다")
    private String category;

    @NotNull(message = "현재 재고는 필수입니다")
    @Min(value = 0, message = "현재 재고는 0 이상이어야 합니다")
    private Integer currentStock;

    @NotNull(message = "안전 재고는 필수입니다")
    @Min(value = 0, message = "안전 재고는 0 이상이어야 합니다")
    private Integer safeStock;

    @NotNull(message = "일일 소비량은 필수입니다")
    @Min(value = 0, message = "일일 소비량은 0 이상이어야 합니다")
    private Double dailyConsumptionRate;

    // GPU 특화 필드
    @Pattern(regexp = "^(RTX 4070|RTX 4070 Super|RTX 4070 Ti|RTX 4070 Ti Super)$", message = "chipset은 RTX 4070 시리즈만 허용됩니다")
    private String chipset;

    private String brand;

    private String modelName;

    @Pattern(regexp = "^\\d+GB$", message = "VRAM은 숫자+GB 형식이어야 합니다 (예: 12GB)")
    private String vram;

    private Boolean isOc;
}
