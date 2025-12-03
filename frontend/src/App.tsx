import { useEffect, useState } from 'react';
import './App.css';
import FundingTable from './components/FundingTable';
import { fetchFundingRates, type MarketOpportunities } from './api';

function App() {
  const [data, setData] = useState<MarketOpportunities | null>(null);
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
        <h1>Lighter Exchange Funding Rates</h1>
        <div className="status-bar">
          {loading && <span className="loading-badge">Updating...</span>}
          {lastUpdated && !loading && (
            <span className="last-updated">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      <main className="dashboard-content">
        {error && <div className="error-message">{error}</div>}

        {data && (
          <div className="tables-grid">
            <FundingTable
              title="Top 10 Long Opportunities (Highest Negative Rate)"
              data={data.top_long}
              type="long"
            />
            <FundingTable
              title="Top 10 Short Opportunities (Highest Positive Rate)"
              data={data.top_short}
              type="short"
            />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Data provided by Lighter Exchange. 2-Day Average Calculation.</p>
      </footer>
    </div>
  );
}

export default App;
