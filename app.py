import os
import time
import asyncio
import schedule
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

import torch
from sentiment import load_finbert, analyze
from data_sources import get_prices, get_news, get_reddit
from alert_bus import emit, PriceAlert, SentimentAlert
from chat_sambanova import say_from_facts
from export_data import export_to_json

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
load_dotenv()

WATCH = [s.strip() for s in os.getenv("WATCH", "AAPL,NVDA,MSFT,BTC-USD,ETH-USD").split(",") if s.strip()]
PRICE_THRESH = float(os.getenv("PRICE_THRESH", 0.005))
BUY_THRESH = float(os.getenv("BUY_THRESH", 0.65))
SELL_THRESH = float(os.getenv("SELL_THRESH", 0.35))
COOLDOWN_MIN = float(os.getenv("COOLDOWN_MIN", 1))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", 15))
PRICE_CALC_MODE = os.getenv("PRICE_CALC_MODE", "day_to_day")

# ---------------------------------------------------------------------
# INITIALIZE FINBERT
# ---------------------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔧 Using device: {device}")

tok, mdl, idx_pos, idx_neg = load_finbert(device=device)
print("✅ FinBERT loaded and ready\n")

# ---------------------------------------------------------------------
# ALERT TRACKING WITH BASELINE PRICES
# ---------------------------------------------------------------------
LAST_ALERT = {}
BASELINE_PRICES = {}
LATEST_ANALYSIS = {}

def reset_baseline(symbol: str, price: float):
    """Set new baseline price after alerting."""
    BASELINE_PRICES[symbol] = price
    LAST_ALERT[f"price_{symbol}"] = datetime.now(timezone.utc)

def get_cumulative_change(symbol: str, current_price: float) -> float:
    """Calculate change from last alert baseline."""
    baseline = BASELINE_PRICES.get(symbol)
    if baseline is None:
        BASELINE_PRICES[symbol] = current_price
        return 0.0
    return (current_price - baseline) / baseline

def should_alert_price(symbol: str, change_pct: float, threshold: float) -> bool:
    """Alert on ANY threshold breach (up or down) from baseline."""
    return abs(change_pct) >= threshold

# ---------------------------------------------------------------------
# SENTIMENT + DATA ANALYSIS
# ---------------------------------------------------------------------
async def analyze_symbol(symbol: str):
    """Fetch news & Reddit concurrently, then run FinBERT sentiment analysis."""
    news_task = asyncio.create_task(get_news(symbol))
    reddit_task = asyncio.create_task(get_reddit(symbol))
    news_titles, reddit_texts = await asyncio.gather(news_task, reddit_task)

    result = analyze(
        symbol, news_titles, reddit_texts,
        tok, mdl, idx_pos, idx_neg,
        buy=BUY_THRESH, sell=SELL_THRESH, device=device
    )
    return result, news_titles, reddit_texts

# ---------------------------------------------------------------------
# MONITORING LOOP
# ---------------------------------------------------------------------
async def run_cycle_async():
    """Main monitoring cycle: prices → sentiment → alerts."""
    now = datetime.now()
    market_status = "🟢 LIVE" if now.weekday() < 5 and 9 <= now.hour < 16 else "🔴 CLOSED"
    print(f"\n[{now:%Y-%m-%d %H:%M:%S}] {market_status} 🔄 Monitoring {len(WATCH)} symbols...")

    intraday_mode = PRICE_CALC_MODE == "intraday"
    prices = get_prices(WATCH, intraday=intraday_mode)

    # ----- PRICE ALERTS -----
    for symbol, price_data in prices.items():
        current_price = price_data["price"]
        trading_date = price_data.get("trading_date", "")
        is_live = price_data.get("is_live", False)
        
        cumulative_change = get_cumulative_change(symbol, current_price)
        baseline = BASELINE_PRICES.get(symbol, current_price)
        
        status_emoji = "📊" if is_live else "📅"
        print(f"  {status_emoji} {symbol}: ${current_price:.2f} "
              f"(baseline: ${baseline:.2f}, change: {cumulative_change*100:+.2f}%) [{trading_date}]")

        if should_alert_price(symbol, cumulative_change, PRICE_THRESH):
            direction = "up" if cumulative_change > 0 else "down"
            
            emit(PriceAlert(
                type="price", symbol=symbol, direction=direction,
                change_pct=round(cumulative_change * 100, 2),
                price=round(current_price, 2),
                prev_close=round(baseline, 2),
                ts=time.time(), trading_date=trading_date
            ))
            
            reset_baseline(symbol, current_price)
            print(f"  🔔 Price alert! New baseline: ${current_price:.2f}")

    # ----- SENTIMENT ANALYSIS (SILENT) -----
    results = await asyncio.gather(*[analyze_symbol(symbol) for symbol in WATCH])

    for i, symbol in enumerate(WATCH):
        result, news_titles, reddit_texts = results[i]
        if not result:
            continue

        # Store latest analysis for on-demand queries
        LATEST_ANALYSIS[symbol] = {
            "decision": result["decision"],
            "confidence": result["confidence"],
            "price": prices.get(symbol, {}).get("price"),
            "change_from_baseline": get_cumulative_change(symbol, prices.get(symbol, {}).get("price", 0)) * 100,
            "news_count": result["news_count"],
            "reddit_count": result["reddit_count"],
            "positive": result["positive"],
            "negative": result["negative"],
            "avg_sentiment": result["avg_sentiment"],
            "news_topics": result["news_topics"],
            "reddit_topics": result["reddit_topics"],
            "sample_titles": result["sample_titles"],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"  📰 {symbol} sentiment: {result['decision']} ({result['confidence']:.1f}% confidence) "
              f"[{result['news_count']} news, {result['reddit_count']} reddit]")

    # Export for Alexa/CLI consumption
    export_to_json(LATEST_ANALYSIS)

# ---------------------------------------------------------------------
# SCHEDULER
# ---------------------------------------------------------------------
def run_cycle():
    asyncio.run(run_cycle_async())

def run_loop():
    run_cycle()
    schedule.every(POLL_SECONDS).seconds.do(run_cycle)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ---------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 FinGalaxy Model Backend Online")
    print("=" * 70)
    print(f"📊 Watching: {', '.join(WATCH)}")
    print(f"📈 Price threshold: ±{PRICE_THRESH * 100:.2f}%")
    print(f"🔄 Poll interval: {POLL_SECONDS}s")
    print(f"💡 Device: {device}")
    print("=" * 70 + "\n")

    try:
        run_loop()
    except KeyboardInterrupt:
        print("\n👋 Shutting down FinGalaxy...")
