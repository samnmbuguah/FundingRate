import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import app, db, FundingRate
from datetime import datetime, timedelta

with app.app_context():
    # Get total count
    count = FundingRate.query.count()
    print(f"Total records: {count}")
    
    if count > 0:
        # Get time range
        oldest = FundingRate.query.order_by(FundingRate.timestamp.asc()).first()
        newest = FundingRate.query.order_by(FundingRate.timestamp.desc()).first()
        
        print(f"Oldest record: {oldest.timestamp}")
        print(f"Newest record: {newest.timestamp}")
        
        duration = newest.timestamp - oldest.timestamp
        print(f"Data duration: {duration}")
        
        if duration < timedelta(hours=48):
            print("NOTE: Data covers less than 48 hours. The average is currently based on available partial data.")
        else:
            print("Data covers full 48 hours.")
            
        # Check distinct symbols
        symbols = db.session.query(FundingRate.symbol).distinct().count()
        print(f"Unique symbols: {symbols}")
    else:
        print("No data in database.")
