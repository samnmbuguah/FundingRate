# Quick Fix: Replace passenger_wsgi.py on Server

## The Problem
cPanel auto-generated a default `passenger_wsgi.py` file when you created the Python App. Our deployment uploaded the correct file, but it might not have replaced it due to timing or permissions.

## Solution (Choose One)

### Option 1: Via cPanel File Manager (Recommended)
1. Log into cPanel
2. Go to **File Manager**
3. Navigate to `/home/akilnoqy/funding-rate/`
4. Find `passenger_wsgi.py`
5. Right-click → **Edit**
6. Replace ALL contents with:

```python
import sys
import os

# Add the application directory to the python path
sys.path.insert(0, os.path.dirname(__file__))
# Add the backend directory to the python path so imports in app.py work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the application
from backend.app import app as application
```

7. Save the file
8. Go to **Setup Python App** → Click **RESTART**

### Option 2: Via SSH
```bash
ssh -i ~/.ssh/id_rsa_deploy -p 21098 akilnoqy@66.29.146.96
cd ~/funding-rate
# Backup the old file
mv passenger_wsgi.py passenger_wsgi.py.old

# Create the correct file
cat > passenger_wsgi.py << 'EOF'
import sys
import os

# Add the application directory to the python path
sys.path.insert(0, os.path.dirname(__file__))
# Add the backend directory to the python path so imports in app.py work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the application
from backend.app import app as application
EOF

# Touch the file to trigger restart
touch passenger_wsgi.py
```

### Option 3: Re-run Deployment
The `touch passenger_wsgi.py` command in the deployment script should trigger a restart. Try:
```bash
./deploy.sh
```

Then go to cPanel → Setup Python App → **RESTART**

## Verification
After restarting, visit https://fixsimu.com/ - you should see the Funding Rate Dashboard instead of "It works!"
