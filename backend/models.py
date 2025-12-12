from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class FundingRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exchange = db.Column(db.String(32), nullable=False, default='lighter')
    symbol = db.Column(db.String(50), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'rate': self.rate,
            'timestamp': self.timestamp.isoformat()
        }
