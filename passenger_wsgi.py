import os
import sys

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the Flask application
from backend.app import app as application

# The 'application' variable is the WSGI callable that Passenger will use
