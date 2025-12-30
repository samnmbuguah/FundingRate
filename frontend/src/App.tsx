import { useCallback, useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import './App.css';
import FundingTable from './components/FundingTable';
import CryptoDetail from './pages/CryptoDetail';
import { fetchFundingRates, fetchHyenaFundingRates, fetchStatus, type MarketOpportunities, type JobStatus } from './api';


function Dashboard() {
  type Exchange = 'lighter' | 'hyena';

  // Get active exchange from URL logic or props could work, 
  // but better to just use separate routes rendering Dashboard with propped exchange
  const location = useLocation();
  const activeExchange: Exchange = location.pathname === '/hyena' ? 'hyena' : 'lighter';

  const [data, setData] = useState<MarketOpportunities>({ top_long: [], top_short: [], timestamp: '' });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);

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
    // Since data is cached in database, we can poll less frequently
    // Lighter updates every 10s, Hyperliquid updates via cron (typically every minute)
    const interval = setInterval(loadData, activeExchange === 'lighter' ? 10000 : 30000);
    return () => clearInterval(interval);
  }, [loadData, activeExchange]);

  // Poll backend job status for display in footer
  useEffect(() => {
    const poll = async () => {
      try {
        const status = await fetchStatus();
        setJobStatus(status);
      } catch (e) {
        // Non-fatal; keep prior status
        console.error('Failed to fetch status', e);
      }
    };
    poll();
    const t = setInterval(poll, 10000);
    return () => clearInterval(t);
  }, []);

  const title = activeExchange === 'lighter' ? 'Lighter Funding Rates' : 'HyENA Funding Rates';
  const footerCopy = activeExchange === 'lighter'
    ? 'Data provided by Lighter Exchange • 3-Day Average Calculation'
    : 'Data provided by HyENA (hyena.trade) • USDe Margin • 3-Day Average Calculation';

  return (
    <div className="app-container">
      <header className="app-header">
        <div>
          <h1>{title}</h1>
          <div className="exchange-tabs">
            <Link to="/">
              <button
                className={`exchange-tab ${activeExchange === 'lighter' ? 'active' : ''}`}
                disabled={activeExchange === 'lighter'}
              >
                Lighter
              </button>
            </Link>
            <Link to="/hyena">
              <button
                className={`exchange-tab ${activeExchange === 'hyena' ? 'active' : ''}`}
                disabled={activeExchange === 'hyena'}
              >
                HyENA
              </button>
            </Link>
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
              enableNavigation={true}
              exchange={activeExchange}
            />
            <FundingTable
              title="Top 10 Short Opportunities"
              data={data.top_short}
              type="short"
              nextFundingTime={data.next_funding_time}
              enableNavigation={true}
              exchange={activeExchange}
            />
          </div>
        )}
      </div>

      <footer className="app-footer">
        <p>{footerCopy}</p>
        {jobStatus && (
          <div className="job-status">
            <strong>Status:</strong> {jobStatus.status}
            {jobStatus.job && <> • <strong>Job:</strong> {jobStatus.job}</>}
            {typeof jobStatus.current === 'number' && typeof jobStatus.total === 'number' && (
              <> • <strong>Progress:</strong> {jobStatus.current}/{jobStatus.total}</>
            )}
            {jobStatus.stored !== undefined && (
              <> • <strong>Stored:</strong> {jobStatus.stored}</>
            )}
            {jobStatus.error && (
              <> • <strong>Error:</strong> {jobStatus.error}</>
            )}
          </div>
        )}
      </footer>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/hyena" element={<Dashboard />} />
        <Route path="/crypto/:symbol" element={<CryptoDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
