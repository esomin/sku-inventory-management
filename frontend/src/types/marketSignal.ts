/**
 * Market Signal Response interface for community signal data returned from the API
 * Validates: Requirements 11.1, 11.2, 11.3
 */
export interface MarketSignalResponse {
    id: number;
    keyword: string;
    postTitle: string;
    postUrl: string | null;
    subreddit: string;
    sentimentScore: number | null;
    mentionCount: number;
    date: string;
    createdAt: string;
}

/**
 * Trending Keyword Response interface for trending keywords
 * Validates: Requirements 11.2
 */
export interface TrendingKeywordResponse {
    keyword: string;
    mentionCount: number;
    weekOverWeekGrowth: number;
    topPosts: {
        title: string;
        url: string;
        subreddit: string;
    }[];
}

/**
 * Parameters for getMarketSignals method
 * Validates: Requirements 11.1, 11.3
 */
export interface GetMarketSignalsParams {
    startDate?: string;
    endDate?: string;
    keyword?: string;
}
