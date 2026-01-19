import axios, { AxiosError } from 'axios';
import { toast } from 'sonner';
import type { SKURequest, SKUResponse, PageResponse } from '../types/sku';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

/**
 * Axios instance configured for SKU API
 */
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Error interceptor for handling API errors with toast notifications
 * Validates: Requirements 9.3, 9.4, 10.4
 */
apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError<{ message?: string }>) => {
        if (error.response) {
            // Server responded with error status
            const { status, data } = error.response;
            const message = data?.message || '알 수 없는 오류가 발생했습니다';

            switch (status) {
                case 404:
                    toast.error('요청한 리소스를 찾을 수 없습니다');
                    break;
                case 409:
                    toast.error('중복된 SKU 코드입니다');
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
            // Request made but no response received
            toast.error('서버에 연결할 수 없습니다');
        } else {
            // Error in request setup
            toast.error('요청 중 오류가 발생했습니다');
        }

        return Promise.reject(error);
    }
);

/**
 * Parameters for getAllSKUs method
 */
export interface GetAllSKUsParams {
    searchTerm?: string;
    category?: string;
    problemStockOnly?: boolean;
    page?: number;
    size?: number;
    sortBy?: string;
    sortDirection?: 'ASC' | 'DESC';
}

/**
 * SKU API client with CRUD operations
 * Validates: Requirements 1.1, 2.1, 2.3, 3.1, 4.1
 */
export const skuApi = {
    /**
     * Get all SKUs with optional filtering, sorting, and pagination
     * Validates: Requirements 2.1
     */
    getAll: (params: GetAllSKUsParams = {}) => {
        return apiClient.get<PageResponse<SKUResponse>>('/skus', { params });
    },

    /**
     * Get a single SKU by ID
     * Validates: Requirements 2.3
     */
    getById: (id: number) => {
        return apiClient.get<SKUResponse>(`/skus/${id}`);
    },

    /**
     * Create a new SKU
     * Validates: Requirements 1.1
     */
    create: (data: SKURequest) => {
        return apiClient.post<SKUResponse>('/skus', data);
    },

    /**
     * Update an existing SKU
     * Validates: Requirements 3.1
     */
    update: (id: number, data: SKURequest) => {
        return apiClient.put<SKUResponse>(`/skus/${id}`, data);
    },

    /**
     * Delete a SKU
     * Validates: Requirements 4.1
     */
    delete: (id: number) => {
        return apiClient.delete(`/skus/${id}`);
    },
};
