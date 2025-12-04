import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { FundingRateData } from '../api';
import CryptoLogo from './CryptoLogo';

interface FundingTableProps {
    title: string;
    data: FundingRateData[];
    type: 'long' | 'short';
    nextFundingTime?: string;
}

const FundingTable: React.FC<FundingTableProps> = ({ title, data, type, nextFundingTime }) => {
    const navigate = useNavigate();
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [timeLeft, setTimeLeft] = useState<string>('');

    useEffect(() => {
        if (!nextFundingTime) return;

        const updateTimer = () => {
            const now = new Date();
            const target = new Date(nextFundingTime);
            const diff = target.getTime() - now.getTime();

            if (diff <= 0) {
                setTimeLeft('00:00:00');
                return;
            }

            const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
            const minutes = Math.floor((diff / (1000 * 60)) % 60);
            const seconds = Math.floor((diff / 1000) % 60);

            setTimeLeft(
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
            );
        };

        updateTimer();
        const interval = setInterval(updateTimer, 1000);
        return () => clearInterval(interval);
    }, [nextFundingTime]);

    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const currentData = data.slice(startIndex, startIndex + itemsPerPage);

    const handlePrev = () => {
        setCurrentPage((prev) => Math.max(prev - 1, 1));
    };

    const handleNext = () => {
        setCurrentPage((prev) => Math.min(prev + 1, totalPages));
    };

    const handleRowClick = (symbol: string) => {
        navigate(`/crypto/${symbol}`);
    };

    const handleItemsPerPageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setItemsPerPage(Number(e.target.value));
        setCurrentPage(1); // Reset to first page
    };

    return (
        <div className="funding-table-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                <h2 className={`table-title ${type}`} style={{ margin: 0, border: 'none', padding: 0 }}>{title}</h2>
                {nextFundingTime && (
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>Next Funding:</span>
                        <span style={{ fontFamily: 'monospace', fontWeight: 'bold', color: 'var(--accent-color)' }}>{timeLeft}</span>
                    </div>
                )}
            </div>

            <div className="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>3-Day Avg Rate</th>
                            <th>APR (Annualized)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {currentData.map((item) => {
                            return (
                                <tr
                                    key={item.symbol}
                                    onClick={() => handleRowClick(item.symbol)}
                                    style={{ cursor: 'pointer' }}
                                >
                                    <td className="symbol-cell">
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                            <CryptoLogo symbol={item.symbol} />
                                            {item.symbol}
                                        </div>
                                    </td>
                                    <td className={`rate-cell ${item.average_3day_rate > 0 ? 'positive' : 'negative'}`}>
                                        {(item.average_3day_rate * 100).toFixed(4)}%
                                    </td>
                                    <td className={`rate-cell ${item.apr > 0 ? 'positive' : 'negative'}`}>
                                        {(item.apr * 100).toFixed(2)}%
                                    </td>
                                </tr>
                            );
                        })}
                        {data.length === 0 && (
                            <tr>
                                <td colSpan={4} className="empty-message">No data available</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div className="pagination-controls">
                <div className="items-per-page">
                    <label htmlFor={`items-per-page-${type}`}>Show:</label>
                    <select
                        id={`items-per-page-${type}`}
                        value={itemsPerPage}
                        onChange={handleItemsPerPageChange}
                        className="pagination-select"
                    >
                        <option value={5}>5</option>
                        <option value={10}>10</option>
                        <option value={20}>20</option>
                        <option value={50}>50</option>
                    </select>
                </div>

                <div className="pagination-actions">
                    <button
                        onClick={handlePrev}
                        disabled={currentPage === 1}
                        className="pagination-btn"
                    >
                        Previous
                    </button>
                    <span className="pagination-info">
                        Page {currentPage} of {totalPages}
                    </span>
                    <button
                        onClick={handleNext}
                        disabled={currentPage === totalPages}
                        className="pagination-btn"
                    >
                        Next
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FundingTable;
