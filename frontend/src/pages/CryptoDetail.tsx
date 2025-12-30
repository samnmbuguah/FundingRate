import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchSymbolHistory, fetchHyperliquidSymbolHistory, type HistoricalRate } from '../api';
import CryptoLogo from '../components/CryptoLogo';

const CryptoDetail: React.FC = () => {
    const { symbol } = useParams<{ symbol: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const state = location.state as { exchange?: 'lighter' | 'hyena' } | null;
    const exchange = state?.exchange ?? 'lighter';
    const [history, setHistory] = useState<HistoricalRate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadHistory = async () => {
            if (!symbol) return;
            try {
                const data = exchange === 'hyena'
                    ? await fetchHyperliquidSymbolHistory(symbol)
                    : await fetchSymbolHistory(symbol);
                setHistory(data);
            } catch (err) {
                setError('Failed to load historical data');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        loadHistory();
    }, [symbol]);

    if (loading) {
        return (
            <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
                <div className="loading-badge">Loading history...</div>
            </div>
        );
    }

    if (error || !symbol) {
        return (
            <div className="app-container">
                <div className="error-message">{error || 'Symbol not found'}</div>
                <button onClick={() => navigate('/')} className="pagination-btn">
                    Back to Dashboard
                </button>
            </div>
        );
    }

    // Format data for chart
    const chartData = history.map(item => ({
        time: new Date(item.timestamp).toLocaleDateString() + ' ' + new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        rate: item.rate * 100 // Convert to percentage
    }));

    return (
        <div className="app-container">
            <div className="app-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button
                        onClick={() => navigate('/')}
                        className="pagination-btn"
                        style={{ marginRight: '1rem' }}
                    >
                        ← Back
                    </button>
                    <CryptoLogo symbol={symbol} size={48} />
                    <h1>{symbol} Funding Rate History ({exchange === 'hyena' ? 'HyENA' : 'Lighter'})</h1>
                </div>
            </div>

            <div className="funding-table-container">
                <h2 className="table-title">7-Day Funding Rate History</h2>
                <div style={{ width: '100%', height: 400 }}>
                    <ResponsiveContainer>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="time"
                                stroke="#94a3b8"
                                tick={{ fontSize: 12 }}
                                minTickGap={50}
                            />
                            <YAxis
                                stroke="#94a3b8"
                                tick={{ fontSize: 12 }}
                                tickFormatter={(value) => `${value.toFixed(4)}%`}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                itemStyle={{ color: '#38bdf8' }}
                                formatter={(value: number) => [`${value.toFixed(6)}%`, 'Funding Rate']}
                            />
                            <Line
                                type="monotone"
                                dataKey="rate"
                                stroke="#38bdf8"
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 6 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default CryptoDetail;
