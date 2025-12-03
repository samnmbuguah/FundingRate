import React, { useState } from 'react';
import type { FundingRateData } from '../api';

interface FundingTableProps {
    title: string;
    data: FundingRateData[];
    type: 'long' | 'short';
}

const FundingTable: React.FC<FundingTableProps> = ({ title, data, type }) => {
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 5; // Show 5 items per page for better mobile view, or 10 if preferred

    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const currentData = data.slice(startIndex, startIndex + itemsPerPage);

    const handlePrev = () => {
        setCurrentPage((prev) => Math.max(prev - 1, 1));
    };

    const handleNext = () => {
        setCurrentPage((prev) => Math.min(prev + 1, totalPages));
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
                            <tr key={item.symbol}>
                                <td className="symbol-cell">{item.symbol}</td>
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

            {data.length > itemsPerPage && (
                <div className="pagination-controls">
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
            )}
        </div>
    );
};

export default FundingTable;
