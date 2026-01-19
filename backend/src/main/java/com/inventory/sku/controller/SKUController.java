package com.inventory.sku.controller;

import com.inventory.sku.dto.SKURequest;
import com.inventory.sku.dto.SKUResponse;
import com.inventory.sku.service.SKUService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/skus")
@CrossOrigin(origins = "http://localhost:5173") // Vite 기본 포트
@RequiredArgsConstructor
public class SKUController {

    private final SKUService skuService;

    /**
     * SKU를 생성합니다.
     * 
     * @param request SKU 생성 요청
     * @return 생성된 SKU
     */
    @PostMapping
    public ResponseEntity<SKUResponse> createSKU(@Valid @RequestBody SKURequest request) {
        SKUResponse response = skuService.createSKU(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * ID로 SKU를 조회합니다.
     * 
     * @param id SKU ID
     * @return SKU 정보
     */
    @GetMapping("/{id}")
    public ResponseEntity<SKUResponse> getSKU(@PathVariable Long id) {
        SKUResponse response = skuService.getSKUById(id);
        return ResponseEntity.ok(response);
    }

    /**
     * SKU 목록을 조회합니다 (검색, 필터링, 정렬, 페이징 지원).
     * 
     * @param searchTerm       검색어 (SKU 코드 또는 제품명)
     * @param category         카테고리 필터
     * @param problemStockOnly 문제 재고만 조회 여부
     * @param page             페이지 번호 (0부터 시작)
     * @param size             페이지 크기
     * @param sortBy           정렬 기준 컬럼
     * @param sortDirection    정렬 방향 (ASC/DESC)
     * @return SKU 페이지
     */
    @GetMapping
    public ResponseEntity<Page<SKUResponse>> getAllSKUs(
            @RequestParam(required = false) String searchTerm,
            @RequestParam(required = false) String category,
            @RequestParam(required = false, defaultValue = "false") Boolean problemStockOnly,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "id") String sortBy,
            @RequestParam(defaultValue = "ASC") String sortDirection) {
        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<SKUResponse> response = skuService.getAllSKUs(
                searchTerm, category, problemStockOnly, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * SKU를 수정합니다.
     * 
     * @param id      SKU ID
     * @param request SKU 수정 요청
     * @return 수정된 SKU
     */
    @PutMapping("/{id}")
    public ResponseEntity<SKUResponse> updateSKU(
            @PathVariable Long id,
            @Valid @RequestBody SKURequest request) {
        SKUResponse response = skuService.updateSKU(id, request);
        return ResponseEntity.ok(response);
    }

    /**
     * SKU를 삭제합니다.
     * 
     * @param id SKU ID
     * @return 204 No Content
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteSKU(@PathVariable Long id) {
        skuService.deleteSKU(id);
        return ResponseEntity.noContent().build();
    }

    /**
     * 칩셋으로 SKU 목록을 조회합니다.
     * 
     * @param chipset       칩셋 (예: "RTX 4070 Super")
     * @param page          페이지 번호 (0부터 시작)
     * @param size          페이지 크기
     * @param sortBy        정렬 기준 컬럼
     * @param sortDirection 정렬 방향 (ASC/DESC)
     * @return SKU 페이지
     */
    @GetMapping("/by-chipset")
    public ResponseEntity<Page<SKUResponse>> getSKUsByChipset(
            @RequestParam String chipset,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "id") String sortBy,
            @RequestParam(defaultValue = "ASC") String sortDirection) {
        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<SKUResponse> response = skuService.getSKUsByChipset(chipset, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * 브랜드로 SKU 목록을 조회합니다.
     * 
     * @param brand         브랜드 (예: "ASUS")
     * @param page          페이지 번호 (0부터 시작)
     * @param size          페이지 크기
     * @param sortBy        정렬 기준 컬럼
     * @param sortDirection 정렬 방향 (ASC/DESC)
     * @return SKU 페이지
     */
    @GetMapping("/by-brand")
    public ResponseEntity<Page<SKUResponse>> getSKUsByBrand(
            @RequestParam String brand,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "id") String sortBy,
            @RequestParam(defaultValue = "ASC") String sortDirection) {
        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<SKUResponse> response = skuService.getSKUsByBrand(brand, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * 여러 SKU를 비교합니다.
     * 
     * @param ids SKU ID 목록 (쉼표로 구분)
     * @return SKU 응답 목록
     */
    @GetMapping("/compare")
    public ResponseEntity<java.util.List<SKUResponse>> compareSKUs(
            @RequestParam String ids) {
        java.util.List<Long> idList = java.util.Arrays.stream(ids.split(","))
                .map(String::trim)
                .map(Long::parseLong)
                .collect(java.util.stream.Collectors.toList());

        java.util.List<SKUResponse> response = skuService.compareSKUs(idList);
        return ResponseEntity.ok(response);
    }
}
