import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import FundingTable from './components/FundingTable';
import CryptoDetail from './pages/CryptoDetail';
import { fetchFundingRates, type MarketOpportunities } from './api';

function Dashboard() {
  const [data, setData] = useState<MarketOpportunities>({ top_long: [], top_short: [], timestamp: '' });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadData = async () => {
    try {
      const result = await fetchFundingRates();
      setData(result);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError('Failed to fetch data. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Lighter Funding Rates</h1>
        <div className="status-bar">
          {loading && <span className="loading-badge">Updating...</span>}
          {lastUpdated && (
            <span className="last-updated">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={loadData} className="retry-button">
            Retry
          </button>
        </div>
      )}

      <div className="dashboard-content">
        {data && (
          <div className="tables-grid">
            <FundingTable
              title="Top 10 Long Opportunities"
              data={data.top_long}
              type="long"
              nextFundingTime={data.next_funding_time}
            />
            <FundingTable
              title="Top 10 Short Opportunities"
              data={data.top_short}
              type="short"
              nextFundingTime={data.next_funding_time}
            />
          </div>
        )}
      </div>

      <footer className="app-footer">
        <p>Data provided by Lighter Exchange • 2-Day Average Calculation</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/crypto/:symbol" element={<CryptoDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
