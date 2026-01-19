package com.inventory.sku.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;

@Entity
@Table(name = "skus")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SKU {

    private static final List<String> VALID_CHIPSETS = Arrays.asList(
            "RTX 4070",
            "RTX 4070 Super",
            "RTX 4070 Ti",
            "RTX 4070 Ti Super");

    private static final String GPU_CATEGORY = "그래픽카드";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false, length = 100)
    @NotBlank(message = "SKU 코드는 필수입니다")
    private String skuCode;

    @Column(nullable = false)
    @NotBlank(message = "제품명은 필수입니다")
    private String productName;

    @Column(nullable = false, length = 100)
    @NotBlank(message = "카테고리는 필수입니다")
    private String category;

    @Column(nullable = false)
    @NotNull(message = "현재 재고는 필수입니다")
    @Min(value = 0, message = "현재 재고는 0 이상이어야 합니다")
    private Integer currentStock;

    @Column(nullable = false)
    @NotNull(message = "안전 재고는 필수입니다")
    @Min(value = 0, message = "안전 재고는 0 이상이어야 합니다")
    private Integer safeStock;

    @Column(nullable = false)
    @NotNull(message = "일일 소비량은 필수입니다")
    @Min(value = 0, message = "일일 소비량은 0 이상이어야 합니다")
    private Double dailyConsumptionRate;

    // GPU 특화 필드
    @Column(length = 50)
    private String chipset;

    @Column(length = 50)
    private String brand;

    @Column(length = 200)
    private String modelName;

    @Column(length = 10)
    @Pattern(regexp = "^\\d+GB$", message = "VRAM은 숫자+GB 형식이어야 합니다 (예: 12GB)")
    private String vram;

    @Column
    private Boolean isOc;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        validateGpuFields();
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        validateGpuFields();
        updatedAt = LocalDateTime.now();
    }

    private void validateGpuFields() {
        // GPU 제품인 경우 (chipset이 설정된 경우) 카테고리를 "그래픽카드"로 강제
        if (chipset != null && !chipset.isEmpty()) {
            this.category = GPU_CATEGORY;

            // chipset 유효성 검증
            if (!VALID_CHIPSETS.contains(chipset)) {
                throw new IllegalArgumentException(
                        "chipset은 RTX 4070 시리즈만 허용됩니다: " + String.join(", ", VALID_CHIPSETS));
            }
        }

        // VRAM 형식 검증 (Pattern 어노테이션이 처리하지만 추가 검증)
        if (vram != null && !vram.isEmpty() && !vram.matches("^\\d+GB$")) {
            throw new IllegalArgumentException("VRAM은 숫자+GB 형식이어야 합니다 (예: 12GB)");
        }
    }
}
