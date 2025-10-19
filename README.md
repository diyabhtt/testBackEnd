# CelestialStocks 

Real-time financial sentiment analysis and conversational AI for stocks and crypto, powered by FinBERT and SambaNova LLM.

## Features

- **Real-time Price Monitoring** - Track stocks & crypto with configurable alerts
- **AI Sentiment Analysis** - FinBERT analyzes news + Reddit for BUY/SELL/HOLD signals
- **Conversational AI** - Natural language financial assistant via SambaNova
- **Alexa-Ready** - JSON alerts ready for voice assistant integration
- **Fast & Efficient** - Async I/O, batch ML processing, cumulative tracking

## Technology Stack

- **Python 3.9+** - Core language
- **PyTorch + Transformers** - FinBERT sentiment analysis
- **SambaNova AI** - LLM for conversational responses
- **yfinance** - Real-time market data
- **asyncpraw** - Reddit sentiment analysis
- **httpx** - Async HTTP for news fetching

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/fin-galaxy-backend.git
cd fin-galaxy-backend

# Install dependencies
pip3 install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```
# First run will download FinBERT model (~800MB)
## First Runnutes depending on your connection
python3 app.py
```bash
# First run automatically downloads FinBERT model (~800MB)
# This takes 2-5 minutes depending on internet speedfirst run, the FinBERT model will be automatically downloaded to `model_cache/`. This is a one-time download of approximately 800MB.
python3 app.py
```

**What happens on first run:**Create a `.env` file with:
1. Checks for local model cache in `model_cache/`
2. Downloads FinBERT from Hugging Face Hub if not found
3. Caches model locally for instant future startupsour_sambanova_api_key
4. Begins monitoring stocks/cryptoa-4-Maverick-17B-128E-Instruct
SAMBA_URL=https://api.sambanova.ai/v1
## Configuration

Create a `.env` file with:CE_THRESH=0.005
BUY_THRESH=0.65
```properties=0.35
SAMBA_API_KEY=your_sambanova_api_key
SAMBA_MODEL=Llama-4-Maverick-17B-128E-InstructD=your_reddit_client_id
SAMBA_URL=https://api.sambanova.ai/v1CLIENT_SECRET=your_reddit_client_secret

WATCH=AAPL,MSFT,NVDA,BTC-USD,ETH-USD
PRICE_THRESH=0.005## 🚀 Usage
BUY_THRESH=0.65
SELL_THRESH=0.35 Backend

REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```
t without Alexa)
## Usage```bash














### Example Conversation```python3 interactive_cli.py# In a separate terminal```bash### Interactive CLI (Test without Alexa)```python3 app.py```bash### Run Backend# In a separate terminal
python3 interactive_cli.py
```

### Example Conversation
