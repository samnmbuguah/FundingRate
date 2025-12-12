#!/bin/bash

# Configuration
# UPDATE THESE VARIABLES FOR YOUR ENVIRONMENT
USER="maxqyqjd"
HOST="162.0.215.135"
PORT="21098"
DEST_PATH="/home/maxqyqjd/maxquant.online/" # Deploy to domain folder

echo "🚀 Starting deployment to cPanel (maxquant.online)..."

# 1. Build Frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# 2. Prepare Production Directory
echo "📂 Preparing production files..."
rm -rf production
mkdir -p production
mkdir -p production/public

# Copy entire backend to production/backend to avoid missing files
rsync -av backend/ production/backend/

# Copy Frontend Build to public/ (Passenger serves from here)
mkdir -p production/public
cp -r frontend/dist/* production/public/

# WSGI entrypoint for Passenger
cp passenger_wsgi.py production/

# Create .env for production if needed (or rely on cPanel env vars)
# echo "FLASK_ENV=production" > production/.env

# 3. Deploy to Server
echo "📤 Uploading to server..."
# Ensure destination directory exists
ssh -p $PORT $USER@$HOST "mkdir -p $DEST_PATH"

# Rsync files
rsync -avz -e "ssh -p $PORT" production/ $USER@$HOST:$DEST_PATH

# 4. Post-Deployment (Install Deps & Restart)
echo "🔧 Running post-deployment commands on server..."
ssh -p $PORT $USER@$HOST << 'ENDSSH'
    set -e  # Exit on any error
    
    echo "Activating virtual environment..."
    source /home/maxqyqjd/virtualenv/maxquant.online/3.13/bin/activate
    
    echo "Current Python: $(which python)"
    echo "Python version: $(python --version)"
    
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    echo "Installing dependencies from requirements.txt..."
    cd /home/maxqyqjd/maxquant.online
    pip install -r backend/requirements.txt --verbose
    
    echo "Ensuring Flask instance directory exists and is writable..."
    mkdir -p /home/maxqyqjd/maxquant.online/backend/instance
    chmod 775 /home/maxqyqjd/maxquant.online/backend/instance
    
    echo "Running initial data fetch (lighter + hyperliquid)..."
    python backend/fetch_data.py
    
    echo "Verifying Flask installation..."
    python -c "from importlib.metadata import version; print(f'Flask {version(\"flask\")} installed successfully')"
    
    echo "Restarting application..."
    touch passenger_wsgi.py
    
    echo "✅ Post-deployment steps completed!"
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ Post-deployment failed! Please check the output above."
    exit 1
fi

# 5. Cleanup
echo "🧹 Cleaning up local artifacts..."
rm -rf production

echo "✅ Deployment complete!"
