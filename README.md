# Lighter Exchange Funding Rate Dashboard

A real-time dashboard to monitor funding rates from Lighter Exchange, featuring a Flask backend and a React frontend.

## Features
- **Real-time Monitoring**: Fetches funding rates every minute and displays updates every 10 seconds.
- **Opportunity Analysis**: Calculates 2-Day Average Funding Rates from historical data to identify top Long and Short opportunities.
- **Persistent Storage**: SQLite database stores historical data for accurate calculations.
- **Clean UI**: React-based dashboard with clear tables for easy analysis.

## Tech Stack
- **Backend**: Python 3, Flask, SQLAlchemy, Lighter SDK, Pandas
- **Frontend**: React, Vite, TypeScript
- **Database**: SQLite

## Development Setup

### Backend
1. Navigate to `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python app.py`

### Frontend
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Run the dev server: `npm run dev`

## Production Deployment

For production deployment (e.g., on cPanel), the backend serves both the API and the built frontend:

1. **Build the frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Install backend dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Run in production mode**:
   ```bash
   export FLASK_ENV=production
   python3 backend/app.py
   ```

   Or use the deployment script:
   ```bash
   ./deploy.sh
   ```

4. **Access the application**:
   - The entire application (frontend + API) will be available at `http://your-server:5000`
   - API endpoint: `http://your-server:5000/api/funding_rates`

### cPanel Deployment Notes
- The backend must be deployed on a **non-US server** to avoid geo-blocking from Lighter Exchange API.
- Ensure Python 3.9+ is available on your hosting.
- The SQLite database will be created automatically at `instance/funding_rates.db`.
- For persistent processes on cPanel, consider using a process manager or cron job to keep the Flask app running.

## Environment Variables
- `FLASK_ENV=production` - Enables production mode (serves static frontend files)

