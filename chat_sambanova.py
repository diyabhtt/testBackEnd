# chat_sambanova.py
import os
from sambanova import SambaNova

# Lazy client singleton
_client = None

def get_client():
    """Initialize and cache SambaNova client using environment variables."""
    global _client
    if _client is None:
        api_key = os.getenv("SAMBA_API_KEY")
        base_url = os.getenv("SAMBA_URL", "https://api.sambanova.ai/v1")

        if not api_key:
            return None

        _client = SambaNova(api_key=api_key, base_url=base_url)
    return _client


SYSTEM_PROMPT = (
    "You are a helpful financial assistant. "
    "Use the provided FACTS to answer questions naturally and conversationally. "
    "Keep responses concise (2-3 sentences max). "
    "Never invent data - only use what's provided. "
    "If information is missing, say you don't have that data. "
    "Be friendly and helpful like a knowledgeable friend."
)

def say_from_facts(facts: dict, user_prompt: str) -> str:
    """
    Use SambaNova API to have a conversation grounded in facts.
    The model can be conversational but must only use provided data.
    """
    client = get_client()
    if not client:
        return "[Chat offline – SAMBA_API_KEY missing]"

    try:
        model_name = os.getenv("SAMBA_MODEL", "Llama-4-Maverick-17B-128E-Instruct")

        # Format facts in a natural way for the LLM
        facts_text = f"""
Available data for {facts.get('symbol', 'this stock')}:
- Current Price: ${facts.get('price', 'N/A')}
- Change from baseline: {facts.get('change_pct', 0):.2f}%
- Sentiment Decision: {facts.get('decision', 'N/A')}
- Confidence Level: {facts.get('confidence_pct', 'N/A')}%
- News Articles Analyzed: {facts.get('news_count', 0)}
- Reddit Posts Analyzed: {facts.get('reddit_count', 0)}
- Positive Mentions: {facts.get('positive', 0)}
- Negative Mentions: {facts.get('negative', 0)}
- Average Sentiment Score: {facts.get('avg_sentiment', 0):.3f}
- Top News Topics: {', '.join(list(facts.get('news_topics', {}).keys())[:3]) if facts.get('news_topics') else 'none'}
- Top Reddit Topics: {', '.join(list(facts.get('reddit_topics', {}).keys())[:3]) if facts.get('reddit_topics') else 'none'}
- Latest Headline: {facts.get('sample_title', 'none')}
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{facts_text}\n\nUser Question: {user_prompt}"}
        ]

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.3,  # Slightly higher for more natural conversation
            top_p=0.9,
            max_tokens=150  # Allow longer conversational responses
        )

        message = response.choices[0].message
        if isinstance(message.content, list):
            return message.content[0].get("text", "").strip()
        elif isinstance(message.content, str):
            return message.content.strip()
        else:
            return "[Unexpected response format]"

    except Exception as e:
        return f"[SambaNova error] {e}"

def have_conversation(conversation_history: list, latest_analysis: dict, user_message: str) -> str:
    """
    Multi-turn conversation with context.
    conversation_history: list of {"role": "user/assistant", "content": "..."}
    """
    client = get_client()
    if not client:
        return "[Chat offline – SAMBA_API_KEY missing]"

    try:
        model_name = os.getenv("SAMBA_MODEL", "Llama-4-Maverick-17B-128E-Instruct")

        # Build facts context from all available symbols
        facts_context = "Available market data:\n"
        for symbol, data in latest_analysis.items():
            facts_context += f"\n{symbol}:\n"
            facts_context += f"  Price: ${data.get('price', 'N/A')}, Change: {data.get('change_from_baseline', 0):.2f}%\n"
            facts_context += f"  Sentiment: {data.get('decision', 'N/A')} ({data.get('confidence', 0):.1f}% confidence)\n"
            facts_context += f"  News: {data.get('news_count', 0)} articles, {data.get('positive', 0)} positive, {data.get('negative', 0)} negative\n"

        # Build message chain
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + f"\n\n{facts_context}"}
        ]
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.4,
            top_p=0.9,
            max_tokens=200
        )

        message = response.choices[0].message
        if isinstance(message.content, list):
            return message.content[0].get("text", "").strip()
        elif isinstance(message.content, str):
            return message.content.strip()
        else:
            return "[Unexpected response format]"

    except Exception as e:
        return f"[SambaNova error] {e}"
