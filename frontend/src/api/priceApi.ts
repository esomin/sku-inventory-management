import axios, { AxiosError } from 'axios';
import { toast } from 'sonner';
import type {
    PriceLogResponse,
    LatestPriceResponse,
    GetPriceLogsParams
} from '../types/priceLog';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

/**
 * Axios instance configured for Price Log API
 * Validates: Requirements 10.1, 10.2, 10.3
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
                    toast.error('가격 데이터를 찾을 수 없습니다');
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
 * Price Log API client for fetching price history and trends
 * Validates: Requirements 10.1, 10.2, 10.3
 */
export const priceApi = {
    /**
     * Get price logs for a specific SKU with optional date range filtering
     * Validates: Requirements 10.1, 10.3
     * 
     * @param params - Query parameters including skuId and optional date range
     * @returns Promise with array of price log records
     */
    getPriceLogs: (params: GetPriceLogsParams) => {
        return apiClient.get<PriceLogResponse[]>('/price-logs', { params });
    },

    /**
     * Get the latest price for a specific SKU
     * Validates: Requirements 10.2
     * 
     * @param skuId - The SKU identifier
     * @returns Promise with the most recent price record
     */
    getLatestPrice: (skuId: number) => {
        return apiClient.get<LatestPriceResponse>('/price-logs/latest', {
            params: { skuId }
        });
    },
};
