"""
On-demand query handlers for Alexa skill.
These functions are called when user asks questions.
"""
from chat_sambanova import say_from_facts

def get_news_summary(symbol: str, latest_analysis: dict) -> str:
    """
    User asks: "Alexa, what's the news on Apple?"
    Returns a brief summary of latest news and sentiment.
    """
    if symbol not in latest_analysis:
        return f"I don't have recent data for {symbol}. Please try again in a moment."
    
    data = latest_analysis[symbol]
    
    facts = {
        "symbol": symbol,
        "price": data.get("price", 0),
        "change_pct": data.get("change_from_baseline", 0),
        "news_count": data.get("news_count", 0),
        "reddit_count": data.get("reddit_count", 0),
        "decision": data.get("decision", "HOLD"),
        "confidence": data.get("confidence", 50),
        "positive": data.get("positive", 0),
        "negative": data.get("negative", 0),
        "sample_title": data.get("sample_titles", ["recent market activity"])[0] if data.get("sample_titles") else "recent market activity",
        "news_topics": data.get("news_topics", {}),
        "reddit_topics": data.get("reddit_topics", {})
    }
    
    # Let LLM generate natural response
    response = say_from_facts(facts, f"Summarize the latest news and market sentiment for {symbol}.")
    return response

def get_buy_sell_recommendation(symbol: str, latest_analysis: dict) -> str:
    """
    User asks: "Should I buy or sell Apple stock?"
    Returns recommendation based on latest sentiment analysis.
    """
    if symbol not in latest_analysis:
        return f"I don't have enough data to make a recommendation for {symbol} right now."
    
    data = latest_analysis[symbol]
    
    facts = {
        "symbol": symbol,
        "decision": data["decision"],
        "confidence_pct": data["confidence"],
        "price": data["price"],
        "change_pct": data["change_from_baseline"],
        "news_count": data["news_count"],
        "reddit_count": data["reddit_count"],
        "top_topic": list(data["news_topics"].keys())[0] if data["news_topics"] else "market sentiment",
        "avg_sentiment": data["avg_sentiment"],
        "positive": data["positive"],
        "negative": data["negative"]
    }
    
    response = say_from_facts(facts, f"Should I buy or sell {symbol}? Give me your recommendation.")
    return response

def get_detailed_analysis(symbol: str, latest_analysis: dict) -> dict:
    """
    Return full analysis data for advanced queries.
    This can be used by Alexa to answer follow-up questions.
    """
    if symbol not in latest_analysis:
        return None
    
    return latest_analysis[symbol]

# Example usage in Alexa Lambda function:
"""
def lambda_handler(event, context):
    intent = event['request']['intent']['name']
    symbol = extract_symbol_from_slot(event)  # "AAPL", etc.
    
    # Import latest analysis from your backend (via API/DynamoDB/S3)
    latest_analysis = fetch_latest_analysis()
    
    if intent == "GetNewsIntent":
        response = get_news_summary(symbol, latest_analysis)
        return alexa_response(response)
    
    elif intent == "GetRecommendationIntent":
        response = get_buy_sell_recommendation(symbol, latest_analysis)
        return alexa_response(response)
    
    elif intent == "GetPriceIntent":
        data = latest_analysis.get(symbol, {})
        price = data.get("price")
        change = data.get("change_from_baseline")
        return alexa_response(f"{symbol} is at ${price}, {change:+.2f}% from baseline.")
"""
