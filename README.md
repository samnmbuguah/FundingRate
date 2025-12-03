# Lighter Exchange Funding Rate Dashboard

A real-time dashboard to monitor funding rates from Lighter Exchange, featuring a Flask backend and a React frontend.

## Features
- **Real-time Monitoring**: Fetches funding rates every minute.
- **Opportunity Analysis**: Calculates 2-Day Average Funding Rates to identify top Long and Short opportunities.
- **Clean UI**: React-based dashboard with clear tables for easy analysis.

## Tech Stack
- **Backend**: Python 3, Flask, Lighter SDK, Pandas
- **Frontend**: React, Vite, TypeScript, Tailwind CSS (optional/if used)

## Setup

### Backend
1. Navigate to `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python app.py`

### Frontend
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Run the dev server: `npm run dev`

## Deployment
The backend should be deployed on a non-US server to avoid geo-blocking from Lighter Exchange.
