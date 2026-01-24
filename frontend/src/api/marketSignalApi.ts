import axios, { AxiosError } from 'axios';
import { toast } from 'sonner';
import type {
    MarketSignalResponse,
    TrendingKeywordResponse,
    GetMarketSignalsParams
} from '../types/marketSignal';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

/**
 * Axios instance configured for Market Signal API
 * Validates: Requirements 11.1, 11.2, 11.3
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
                    toast.error('커뮤니티 신호 데이터를 찾을 수 없습니다');
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
 * Market Signal API client for fetching community signals and trends
 * Validates: Requirements 11.1, 11.2, 11.3
 */
export const marketSignalApi = {
    /**
     * Get market signals with optional date range and keyword filtering
     * Validates: Requirements 11.1, 11.3
     * 
     * @param params - Query parameters including optional date range and keyword
     * @returns Promise with array of market signal records
     */
    getMarketSignals: (params: GetMarketSignalsParams = {}) => {
        return apiClient.get<MarketSignalResponse[]>('/market-signals', { params });
    },

    /**
     * Get trending keywords with week-over-week growth metrics
     * Validates: Requirements 11.2
     * 
     * @returns Promise with array of trending keywords and their top posts
     */
    getTrendingKeywords: () => {
        return apiClient.get<TrendingKeywordResponse[]>('/market-signals/trending');
    },
};
