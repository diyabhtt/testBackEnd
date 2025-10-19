from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import json

@dataclass
class PriceAlert:
    type: str
    symbol: str
    direction: str
    change_pct: float
    price: float
    prev_close: float
    ts: float
    trading_date: Optional[str] = None  # Add trading date to alert

@dataclass
class SentimentAlert:
    type: str
    symbol: str
    decision: str
    confidence: float
    price: Optional[float]
    change_pct: Optional[float]
    news_count: int
    reddit_count: int
    positive: int
    negative: int
    avg_sentiment: float
    news_topics: dict
    reddit_topics: dict
    sample_titles: list
    ts: float

def emit(alert):
    """
    Emit alert in JSON format.
    Currently prints to console; extend to publish to SNS/webhook for Alexa.
    """
    payload = asdict(alert)
    payload["iso_time"] = datetime.now(timezone.utc).isoformat()
    
    print("\n" + "="*70)
    print(json.dumps(payload, indent=2))
    print("="*70 + "\n")
    
    # TODO: Add webhook/SNS publishing for Alexa skill integration
    # publish_to_alexa(payload)
