import React from 'react';
import type { FundingRateData } from '../api';

interface FundingTableProps {
    title: string;
    data: FundingRateData[];
    type: 'long' | 'short';
}

const FundingTable: React.FC<FundingTableProps> = ({ title, data, type }) => {
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
                        {data.map((item) => (
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
        </div>
    );
};

export default FundingTable;
