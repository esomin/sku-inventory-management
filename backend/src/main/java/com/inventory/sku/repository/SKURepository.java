package com.inventory.sku.repository;

import com.inventory.sku.entity.SKU;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SKURepository extends JpaRepository<SKU, Long> {

    /**
     * SKU 코드로 SKU를 조회합니다.
     * 
     * @param skuCode SKU 코드
     * @return SKU 엔티티 (Optional)
     */
    Optional<SKU> findBySkuCode(String skuCode);

    /**
     * SKU 코드가 존재하는지 확인합니다.
     * 
     * @param skuCode SKU 코드
     * @return 존재 여부
     */
    boolean existsBySkuCode(String skuCode);

    /**
     * 검색어, 카테고리, 문제 재고 필터를 적용하여 SKU 목록을 조회합니다.
     * 
     * @param searchTerm       검색어 (SKU 코드 또는 제품명에 포함)
     * @param category         카테고리 필터
     * @param problemStockOnly 문제 재고만 조회 여부 (현재 재고 <= 안전 재고)
     * @param pageable         페이징 및 정렬 정보
     * @return SKU 페이지
     */
    @Query("SELECT s FROM SKU s WHERE " +
            "(:searchTerm IS NULL OR :searchTerm = '' OR " +
            "LOWER(s.skuCode) LIKE LOWER(CONCAT('%', :searchTerm, '%')) OR " +
            "LOWER(s.productName) LIKE LOWER(CONCAT('%', :searchTerm, '%'))) " +
            "AND (:category IS NULL OR :category = '' OR s.category = :category) " +
            "AND (:problemStockOnly = false OR s.currentStock <= s.safeStock)")
    Page<SKU> findWithFilters(
            @Param("searchTerm") String searchTerm,
            @Param("category") String category,
            @Param("problemStockOnly") Boolean problemStockOnly,
            Pageable pageable);

    /**
     * 칩셋으로 SKU 목록을 조회합니다.
     * 
     * @param chipset  칩셋 (예: "RTX 4070 Super")
     * @param pageable 페이징 및 정렬 정보
     * @return SKU 페이지
     */
    Page<SKU> findByChipset(String chipset, Pageable pageable);

    /**
     * 브랜드로 SKU 목록을 조회합니다.
     * 
     * @param brand    브랜드 (예: "ASUS")
     * @param pageable 페이징 및 정렬 정보
     * @return SKU 페이지
     */
    Page<SKU> findByBrand(String brand, Pageable pageable);
}
