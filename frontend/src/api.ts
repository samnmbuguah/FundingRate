export interface FundingRateData {
    symbol: string;
    average_3day_rate: number;
    apr: number;
}

export interface MarketOpportunities {
    top_long: FundingRateData[];
    top_short: FundingRateData[];
    timestamp: string;
    next_funding_time?: string;
}

const API_BASE_URL = '/api';

export interface HistoricalRate {
    symbol: string;
    rate: number;
    timestamp: string;
}

export const fetchFundingRates = async (): Promise<MarketOpportunities> => {
    try {
        const response = await fetch(`${API_BASE_URL}/funding_rates`);
        if (!response.ok) {
            throw new Error('Failed to fetch funding rates');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching funding rates:', error);
        throw error;
    }
};

export const fetchHyenaFundingRates = async (): Promise<MarketOpportunities> => {
    try {
        const response = await fetch(`${API_BASE_URL}/hyena/funding_rates`);
        if (!response.ok) {
            throw new Error('Failed to fetch HyENA funding rates');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching HyENA funding rates:', error);
        throw error;
    }
};

export const fetchSymbolHistory = async (symbol: string): Promise<HistoricalRate[]> => {
    const response = await fetch(`${API_BASE_URL}/funding_rates/${symbol}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch history for ${symbol}`);
    }
    return response.json();
};

export const fetchHyperliquidFundingRates = async (): Promise<MarketOpportunities> => {
    try {
        const response = await fetch(`${API_BASE_URL}/hyperliquid/funding_rates`);
        if (!response.ok) {
            throw new Error('Failed to fetch Hyperliquid funding rates');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching Hyperliquid funding rates:', error);
        throw error;
    }
};

export const fetchHyperliquidSymbolHistory = async (symbol: string): Promise<HistoricalRate[]> => {
    const response = await fetch(`${API_BASE_URL}/hyperliquid/funding_rates/${symbol}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch Hyperliquid history for ${symbol}`);
    }
    return response.json();
};
