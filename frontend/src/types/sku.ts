/**
 * SKU Request interface for creating and updating SKU records
 * Validates: Requirements 2.2
 */
export interface SKURequest {
    skuCode: string;
    productName: string;
    category: string;
    currentStock: number;
    safeStock: number;
    dailyConsumptionRate: number;
}

/**
 * SKU Response interface for SKU data returned from the API
 * Validates: Requirements 2.2
 */
export interface SKUResponse {
    id: number;
    skuCode: string;
    productName: string;
    category: string;
    currentStock: number;
    safeStock: number;
    riskLevel: string;
    expectedShortageDate: string | null;
    createdAt: string;
    updatedAt: string;
}

/**
 * Generic paginated response interface
 * Validates: Requirements 2.2
 */
export interface PageResponse<T> {
    content: T[];
    totalElements: number;
    totalPages: number;
    size: number;
    number: number;
}
