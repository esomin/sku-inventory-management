package com.inventory.sku.exception;

public class DuplicateSKUException extends RuntimeException {
    
    public DuplicateSKUException(String message) {
        super(message);
    }
    
    public DuplicateSKUException(String skuCode, boolean isCode) {
        super("SKU 코드가 이미 존재합니다: " + skuCode);
    }
}
