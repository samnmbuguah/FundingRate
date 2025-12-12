import { useCallback, useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import FundingTable from './components/FundingTable';
import CryptoDetail from './pages/CryptoDetail';
import { fetchFundingRates, fetchHyenaFundingRates, type MarketOpportunities } from './api';

function Dashboard() {
  type Exchange = 'lighter' | 'hyena';

  const [activeExchange, setActiveExchange] = useState<Exchange>('lighter');
  const [data, setData] = useState<MarketOpportunities>({ top_long: [], top_short: [], timestamp: '' });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const fetcher = activeExchange === 'lighter' ? fetchFundingRates : fetchHyenaFundingRates;
      const result = await fetcher();
      setData(result);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError('Failed to fetch data. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [activeExchange]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Poll every 10 seconds per exchange
    return () => clearInterval(interval);
  }, [loadData]);

  const title = activeExchange === 'lighter' ? 'Lighter Funding Rates' : 'Hyperliquid Funding Rates';
  const footerCopy = activeExchange === 'lighter'
    ? 'Data provided by Lighter Exchange • 3-Day Average Calculation'
    : 'Data provided by Hyperliquid • 3-Day Average Calculation';

  return (
    <div className="app-container">
      <header className="app-header">
        <div>
          <h1>{title}</h1>
          <div className="exchange-tabs">
            <button
              className={`exchange-tab ${activeExchange === 'lighter' ? 'active' : ''}`}
              onClick={() => setActiveExchange('lighter')}
              disabled={activeExchange === 'lighter'}
            >
              Lighter
            </button>
            <button
              className={`exchange-tab ${activeExchange === 'hyena' ? 'active' : ''}`}
              onClick={() => setActiveExchange('hyena')}
              disabled={activeExchange === 'hyena'}
            >
              Hyperliquid
            </button>
          </div>
        </div>
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
              enableNavigation={activeExchange === 'lighter'}
            />
            <FundingTable
              title="Top 10 Short Opportunities"
              data={data.top_short}
              type="short"
              nextFundingTime={data.next_funding_time}
              enableNavigation={activeExchange === 'lighter'}
            />
          </div>
        )}
      </div>

      <footer className="app-footer">
        <p>{footerCopy}</p>
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
