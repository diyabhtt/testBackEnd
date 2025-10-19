import math
import torch
import collections
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def load_finbert(cache="./model_cache", model_name="yiyanghkust/finbert-tone", device=None):
    """
    Load FinBERT model and tokenizer.
    First run downloads from Hugging Face Hub automatically.
    """
    try:
        # Try to load from local cache first
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache,
            local_files_only=True
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            cache_dir=cache,
            local_files_only=True
        )
    except:
        # First-time download from Hugging Face Hub
        print("📥 Downloading FinBERT model from Hugging Face (~800MB)...")
        print("⏱️  This is a one-time download and will take 2-5 minutes...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache)
        model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache)
        print("✅ Download complete! Model cached for future use.")
    
    if device:
        model = model.to(device)
    
    model.eval()
    
    # Get label indices
    id2label = {int(k): v.lower() for k, v in model.config.id2label.items()}
    idx_pos = next(i for i, l in id2label.items() if l.startswith("pos"))
    idx_neg = next(i for i, l in id2label.items() if l.startswith("neg"))
    
    return tokenizer, model, idx_pos, idx_neg

def sigmoid(x):
    """Sigmoid function for confidence mapping."""
    return 1 / (1 + math.exp(-x))

def batch_score_texts(texts, tokenizer, model, idx_pos, idx_neg, device=None):
    """
    Score multiple texts in a single batch for efficiency.
    Returns list of sentiment scores (positive - negative).
    """
    if not texts:
        return []
    
    # Tokenize in batch
    encoded = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=True
    )
    
    if device:
        encoded = {k: v.to(device) for k, v in encoded.items()}
    
    # Get predictions
    with torch.no_grad():
        logits = model(**encoded).logits
        probs = logits.softmax(dim=1)
    
    # Calculate sentiment scores (pos - neg)
    scores = []
    for i in range(len(texts)):
        score = float(probs[i, idx_pos]) - float(probs[i, idx_neg])
        scores.append(score)
    
    return scores

def explain_topics(texts: list[str], vocab: list[str]) -> dict:
    """
    Extract topic frequencies from texts.
    Returns top 5 topics with normalized frequencies.
    """
    counter = collections.Counter()
    
    for text in texts:
        text_lower = text.lower()
        for word in vocab:
            if word in text_lower:
                counter[word] += 1
    
    top_topics = counter.most_common(5)
    total = sum(counter.values()) or 1
    
    return {word: round(count / total, 3) for word, count in top_topics}

def analyze(symbol, news_titles, reddit_texts, tokenizer, model, idx_pos, idx_neg, 
            buy=0.65, sell=0.35, device=None):
    """
    Analyze sentiment from news and Reddit data.
    Returns comprehensive analysis with decision, confidence, and explainable features.
    """
    # Batch score all texts
    news_scores = batch_score_texts(news_titles, tokenizer, model, idx_pos, idx_neg, device)
    reddit_scores = batch_score_texts(reddit_texts, tokenizer, model, idx_pos, idx_neg, device)
    
    all_scores = news_scores + reddit_scores
    
    if not all_scores:
        return None
    
    # Calculate average sentiment
    avg_sentiment = sum(all_scores) / len(all_scores)
    
    # Base confidence from sentiment strength
    base_confidence = sigmoid(2.0 * avg_sentiment)
    
    # Reliability weighting based on volume (more sources = more reliable)
    reliability = min(1.0, math.log(1 + len(all_scores)) / math.log(51))
    final_confidence = 0.5 + (base_confidence - 0.5) * reliability
    
    # Make decision
    decision = "HOLD"
    if final_confidence >= buy:
        decision = "BUY"
    elif final_confidence <= sell:
        decision = "SELL"
    
    # Explainable features
    news_vocab = [
        "etf", "approval", "ban", "partnership", "surge", "drop",
        "adoption", "guidance", "earnings", "revenue", "profit"
    ]
    reddit_vocab = [
        "halving", "bullish", "bearish", "regulation", "pump", "dump",
        "inflation", "macro", "moon", "crash", "rally"
    ]
    
    return {
        "decision": decision,
        "confidence": round(final_confidence * 100, 1),
        "news_count": len(news_titles),
        "reddit_count": len(reddit_texts),
        "total_analyzed": len(all_scores),
        "positive": sum(1 for s in all_scores if s > 0),
        "negative": sum(1 for s in all_scores if s < 0),
        "avg_sentiment": round(avg_sentiment, 3),
        "news_topics": explain_topics(news_titles, news_vocab),
        "reddit_topics": explain_topics(reddit_texts, reddit_vocab),
        "sample_titles": news_titles[:3]
    }
