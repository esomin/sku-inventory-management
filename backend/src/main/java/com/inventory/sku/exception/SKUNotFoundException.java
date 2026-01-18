package com.inventory.sku.exception;

public class SKUNotFoundException extends RuntimeException {
    
    public SKUNotFoundException(String message) {
        super(message);
    }
    
    public SKUNotFoundException(Long id) {
        super("SKU를 찾을 수 없습니다: " + id);
    }
}
