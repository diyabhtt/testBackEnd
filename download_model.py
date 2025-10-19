"""
Download pre-cached FinBERT model from cloud storage.
Run this once before first use for faster startup.
"""
import os
import requests
from pathlib import Path

MODEL_URL = "https://your-cloud-storage-url.com/finbert_model.tar.gz"
MODEL_CACHE = "./model_cache"

def download_model():
    """Download and extract pre-cached model."""
    cache_path = Path(MODEL_CACHE)
    
    # Check if model already exists
    if cache_path.exists() and any(cache_path.iterdir()):
        print("✅ Model cache already exists!")
        return
    
    print("📥 Downloading FinBERT model (~800MB)...")
    print("This is a one-time download and may take 2-5 minutes...")
    
    cache_path.mkdir(exist_ok=True)
    
    # Download from cloud
    response = requests.get(MODEL_URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Save and extract
    # ... (add extraction logic)
    
    print("✅ Model downloaded successfully!")

if __name__ == "__main__":
    download_model()
