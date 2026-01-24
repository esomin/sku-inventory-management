import axios, { AxiosError } from 'axios';
import { toast } from 'sonner';
import type {
    RiskAlertResponse,
    GetRiskAlertsParams,
    AcknowledgeAlertRequest
} from '../types/riskAlert';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

/**
 * Axios instance configured for Risk Alert API
 * Validates: Requirements 12.3, 12.4
 */
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Error interceptor for handling API errors with toast notifications
 */
apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError<{ message?: string }>) => {
        if (error.response) {
            const { status, data } = error.response;
            const message = data?.message || '알 수 없는 오류가 발생했습니다';

            switch (status) {
                case 404:
                    toast.error('위험 알림을 찾을 수 없습니다');
                    break;
                case 400:
                    toast.error(message || '잘못된 요청입니다');
                    break;
                case 500:
                    toast.error('서버 오류가 발생했습니다');
                    break;
                default:
                    toast.error('오류가 발생했습니다');
            }
        } else if (error.request) {
            toast.error('서버에 연결할 수 없습니다');
        } else {
            toast.error('요청 중 오류가 발생했습니다');
        }

        return Promise.reject(error);
    }
);

/**
 * Risk Alert API client for fetching and managing risk alerts
 * Validates: Requirements 12.3, 12.4
 */
export const riskAlertApi = {
    /**
     * Get risk alerts with optional filtering by acknowledgment status
     * Validates: Requirements 12.3
     * 
     * @param params - Query parameters including optional acknowledged filter
     * @returns Promise with array of risk alert records
     */
    getRiskAlerts: (params: GetRiskAlertsParams = {}) => {
        return apiClient.get<RiskAlertResponse[]>('/risk-alerts', { params });
    },

    /**
     * Acknowledge a risk alert by ID
     * Validates: Requirements 12.4
     * 
     * @param id - The risk alert identifier
     * @returns Promise with the updated risk alert record
     */
    acknowledgeAlert: (id: number) => {
        const data: AcknowledgeAlertRequest = { acknowledged: true };
        return apiClient.put<RiskAlertResponse>(`/risk-alerts/${id}/acknowledge`, data);
    },
};
