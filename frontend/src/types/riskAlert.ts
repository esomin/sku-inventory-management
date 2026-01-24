/**
 * Risk Alert Response interface for risk alert data returned from the API
 * Validates: Requirements 12.3, 12.4
 */
export interface RiskAlertResponse {
    id: number;
    skuId: number;
    productName: string;
    riskIndex: number;
    threshold: number;
    contributingFactors: {
        priceChange?: number;
        sentimentScore?: number;
        newReleaseMentions?: number;
    };
    acknowledged: boolean;
    createdAt: string;
}

/**
 * Parameters for getRiskAlerts method
 * Validates: Requirements 12.3
 */
export interface GetRiskAlertsParams {
    acknowledged?: boolean;
    skuId?: number;
}

/**
 * Request body for acknowledging a risk alert
 * Validates: Requirements 12.4
 */
export interface AcknowledgeAlertRequest {
    acknowledged: boolean;
}
