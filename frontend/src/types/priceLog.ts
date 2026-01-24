/**
 * Price Log Response interface for price data returned from the API
 * Validates: Requirements 10.1, 10.2, 10.3
 */
export interface PriceLogResponse {
    id: number;
    skuId: number;
    price: number;
    source: string;
    sourceUrl: string | null;
    recordedAt: string;
    priceChangePct: number | null;
    createdAt: string;
}

/**
 * Latest Price Response interface for the most recent price of a SKU
 * Validates: Requirements 10.2
 */
export interface LatestPriceResponse {
    skuId: number;
    price: number;
    source: string;
    recordedAt: string;
    priceChangePct: number | null;
}

/**
 * Parameters for getPriceLogs method
 * Validates: Requirements 10.1, 10.3
 */
export interface GetPriceLogsParams {
    skuId: number;
    startDate?: string;
    endDate?: string;
}
