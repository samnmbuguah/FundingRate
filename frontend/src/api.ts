export interface FundingRateData {
    symbol: string;
    average_2day_rate: number;
}

export interface MarketOpportunities {
    top_long: FundingRateData[];
    top_short: FundingRateData[];
    timestamp: string;
}

const API_BASE_URL = 'http://localhost:5000/api';

export const fetchFundingRates = async (): Promise<MarketOpportunities> => {
    try {
        const response = await fetch(`${API_BASE_URL}/funding_rates`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching funding rates:', error);
        throw error;
    }
};
