#!/bin/bash

# Production deployment script for cPanel or similar hosting

echo "🚀 Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "📦 Installing backend dependencies..."
pip install -r backend/requirements.txt

echo "✅ Build complete!"
echo ""
echo "To run in production mode:"
echo "  export FLASK_ENV=production"
echo "  python3 backend/app.py"
echo ""
echo "The app will be available at http://localhost:5000"
echo "Both frontend and API will be served from the same port."
