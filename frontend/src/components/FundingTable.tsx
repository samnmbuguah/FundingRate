import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { FundingRateData } from '../api';
import CryptoLogo from './CryptoLogo';

interface FundingTableProps {
    title: string;
    data: FundingRateData[];
    type: 'long' | 'short';
}

const FundingTable: React.FC<FundingTableProps> = ({ title, data, type }) => {
    const navigate = useNavigate();
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);

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
            <h2 className={`table-title ${type}`}>{title}</h2>
            <div className="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>2-Day Avg Rate (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {currentData.map((item) => (
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
                                <td className={`rate-cell ${item.average_2day_rate > 0 ? 'positive' : 'negative'}`}>
                                    {(item.average_2day_rate * 100).toFixed(4)}%
                                </td>
                            </tr>
                        ))}
                        {data.length === 0 && (
                            <tr>
                                <td colSpan={2} className="empty-message">No data available</td>
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
