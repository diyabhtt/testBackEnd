import os
import asyncio
import httpx
import yfinance as yf
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import urllib.parse

# Subreddits for crypto and stock discussion
SUBREDDITS = [
    "CryptoCurrency", "CryptoMarkets", "Bitcoin", "Ethereum",
    "stocks", "investing", "wallstreetbets", "StockMarket"
]

# Symbol aliases for better search coverage
ALIASES = {
    "BTC-USD": ["bitcoin", "btc"],
    "ETH-USD": ["ethereum", "eth"],
}

UA = {"User-Agent": "FinGalaxy/1.0"}

def now_utc():
    return datetime.now(timezone.utc).timestamp()

async def fetch_google_news(client: httpx.AsyncClient, query: str) -> list:
    """Fetch news headlines from Google News RSS feed."""
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    titles = []
    
    try:
        r = await client.get(url, headers=UA, timeout=10, follow_redirects=True)
        if r.status_code != 200:
            return titles
            
        # Handle empty responses
        if not r.text or len(r.text.strip()) == 0:
            return titles
            
        root = ET.fromstring(r.text)
        
        for item in root.findall(".//item")[:20]:
            title = item.findtext("title")
            if title and title.strip():
                titles.append(title.strip())
    except ET.ParseError:
        # Silent fail - RSS sometimes returns empty/malformed content
        pass
    except Exception as e:
        # Only log unexpected errors
        if "no element found" not in str(e).lower():
            print(f"News fetch error for {query}: {e}")
    
    return titles

async def get_news(symbol: str) -> list[str]:
    """
    Fetch news for a symbol using multiple query terms.
    Deduplicates while preserving order.
    """
    queries = ALIASES.get(symbol, [symbol])
    
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[fetch_google_news(client, q) for q in queries],
            return_exceptions=True
        )
    
    # Deduplicate while keeping order
    seen = set()
    output = []
    
    for result in results:
        if isinstance(result, list):
            for title in result:
                if title not in seen:
                    seen.add(title)
                    output.append(title)
    
    return output[:30]

def reddit_client():
    """Initialize Async Reddit client if credentials are available."""
    try:
        import asyncpraw
        client_id = os.getenv("REDDIT_CLIENT_ID", "")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        username = os.getenv("REDDIT_USERNAME", "")
        password = os.getenv("REDDIT_PASSWORD", "")
        user_agent = os.getenv("REDDIT_USER_AGENT", "FinGalaxy/1.0")
        
        if not client_id or not client_secret:
            return None
            
        return asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
    except ImportError:
        print("asyncpraw not installed. Install with: pip3 install asyncpraw")
        return None
    except Exception as e:
        print(f"Reddit client init failed: {e}")
        return None

async def get_reddit(symbol: str) -> list:
    """
    Fetch Reddit discussions for a symbol using Async PRAW.
    Falls back to JSON API if async PRAW unavailable.
    """
    rc = reddit_client()
    texts = []
    base = symbol.split("-")[0].lower()
    terms = ALIASES.get(symbol, [symbol, base])

    if rc:
        # Use Async PRAW (proper async support)
        try:
            for sub in SUBREDDITS:
                try:
                    subreddit = await rc.subreddit(sub)
                    for query in terms:
                        async for submission in subreddit.search(query, limit=15, sort="new"):
                            text = f"{submission.title} {submission.selftext or ''}".strip()
                            if text:
                                texts.append(text)
                except Exception as e:
                    # Silent fail for individual subreddit errors
                    pass
            
            await rc.close()
            return dedupe_list(texts)[:60]
        except Exception as e:
            print(f"Async PRAW error: {e}")
            try:
                await rc.close()
            except:
                pass

    # Fallback: public JSON API (rate-limited)
    async with httpx.AsyncClient() as client:
        for sub in SUBREDDITS:
            for query in terms:
                url = f"https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=1&sort=new&t=day&limit=20"
                try:
                    r = await client.get(url, headers=UA, timeout=10)
                    if r.status_code != 200:
                        continue
                    
                    data = r.json().get("data", {}).get("children", [])
                    for child in data:
                        d = child.get("data", {})
                        text = f"{d.get('title', '')} {d.get('selftext', '')}".strip()
                        if text:
                            texts.append(text)
                except Exception:
                    # Silent fail for rate limits
                    continue
    
    return dedupe_list(texts)[:60]

def dedupe_list(items: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    output = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output

def get_prices(symbols: list, use_history: bool = False, intraday: bool = False) -> dict:
    """
    Fetch current prices using yfinance.
    
    Args:
        intraday: If True, calculates same-day open-to-close change (like Google)
                  If False, calculates day-to-day close-to-close change
    """
    output = {}
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            
            if len(hist) >= 1:
                # Show recent history only in debug mode
                if debug_mode:
                    print(f"\n{sym} Recent History:")
                    for idx in range(min(3, len(hist))):
                        date = hist.index[-(idx+1)].strftime("%Y-%m-%d %a")
                        close = hist['Close'].iloc[-(idx+1)]
                        print(f"  {date}: ${close:.2f}")
                
                # Most recent trading day
                latest = hist.iloc[-1]
                price = float(latest['Close'])
                trading_date = hist.index[-1].strftime("%Y-%m-%d %a")
                
                if intraday:
                    # Same-day change: Open → Close (like Google)
                    open_price = float(latest['Open'])
                    change_pct = (price - open_price) / open_price
                    prev = open_price
                    comparison = f"Open: ${open_price:.2f} → Close: ${price:.2f}"
                else:
                    # Day-to-day change: Previous Close → Current Close
                    if len(hist) >= 2:
                        prev = float(hist.iloc[-2]['Close'])
                    else:
                        fi = ticker.fast_info
                        prev = float(getattr(fi, "previous_close", price))
                    
                    change_pct = (price - prev) / prev
                    comparison = f"Prev Close: ${prev:.2f} → Close: ${price:.2f}"
                
                if debug_mode:
                    change_dollars = price - prev
                    print(f"  → {comparison}")
                    print(f"  → ${change_dollars:+.2f} ({change_pct*100:+.2f}%)\n")
                
                output[sym] = {
                    "price": price,
                    "prev": prev,
                    "change_pct": change_pct,
                    "trading_date": trading_date,
                    "comparison": comparison,
                    "is_live": hist.index[-1].date() == datetime.now().date()
                }
            else:
                # Fallback to fast_info
                fi = ticker.fast_info
                price = getattr(fi, "last_price", None)
                prev = getattr(fi, "previous_close", None)
                
                if price and prev:
                    change_pct = (price - prev) / prev
                    output[sym] = {
                        "price": float(price),
                        "prev": float(prev),
                        "change_pct": float(change_pct),
                        "trading_date": "unknown",
                        "comparison": "unknown",
                        "is_live": False
                    }
        except Exception as e:
            print(f"Price fetch error for {sym}: {e}")
    
    return output
