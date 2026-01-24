package com.inventory.sku.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "market_signals")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class MarketSignal {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    @NotBlank(message = "키워드는 필수입니다")
    private String keyword;

    @Column(name = "sentiment_score", precision = 5, scale = 2)
    private BigDecimal sentimentScore;

    @Column(name = "mention_count", nullable = false)
    @NotNull(message = "언급 횟수는 필수입니다")
    @Min(value = 1, message = "언급 횟수는 1 이상이어야 합니다")
    private Integer mentionCount = 1;

    @Column(nullable = false)
    @NotNull(message = "날짜는 필수입니다")
    private LocalDate date;

    @Column(name = "post_title", nullable = false, columnDefinition = "TEXT")
    @NotBlank(message = "게시물 제목은 필수입니다")
    private String postTitle;

    @Column(name = "post_url", length = 500)
    private String postUrl;

    @Column(nullable = false, length = 50)
    @NotBlank(message = "서브레딧은 필수입니다")
    private String subreddit;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
