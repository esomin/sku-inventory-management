import axios, { AxiosError } from 'axios';
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
 * Error interceptor for handling API errors
 * Validates: Requirements 1.1, 2.1, 2.3, 3.1, 4.1
 */
apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        if (error.response) {
            // Server responded with error status
            const { status, data } = error.response;

            switch (status) {
                case 404:
                    console.error('Resource not found:', data);
                    break;
                case 409:
                    console.error('Duplicate SKU code:', data);
                    break;
                case 400:
                    console.error('Bad request:', data);
                    break;
                case 500:
                    console.error('Server error:', data);
                    break;
                default:
                    console.error('API error:', data);
            }
        } else if (error.request) {
            // Request made but no response received
            console.error('Network error: Unable to reach server');
        } else {
            // Error in request setup
            console.error('Request error:', error.message);
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
