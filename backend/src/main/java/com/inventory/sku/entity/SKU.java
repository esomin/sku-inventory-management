package com.inventory.sku.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "skus")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SKU {
    
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
    
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @Column(nullable = false)
    private LocalDateTime updatedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
