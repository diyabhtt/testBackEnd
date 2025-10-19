"""
Simple Flask server for Alexa to query latest analysis.
"""
from flask import Flask, jsonify, request
from alexa_queries import get_news_summary, get_buy_sell_recommendation
import json
import os

app = Flask(__name__)

def load_latest_analysis():
    """Load the latest analysis from JSON file."""
    with open('latest_analysis.json', 'r') as f:
        return json.load(f).get('symbols', {})

@app.route('/alexa/news/<symbol>', methods=['GET'])
def alexa_news(symbol):
    """Endpoint for news queries."""
    symbol = symbol.upper()
    analysis = load_latest_analysis()
    response = get_news_summary(symbol, analysis)
    return jsonify({"speech": response})

@app.route('/alexa/recommendation/<symbol>', methods=['GET'])
def alexa_recommendation(symbol):
    """Endpoint for buy/sell recommendations."""
    symbol = symbol.upper()
    analysis = load_latest_analysis()
    response = get_buy_sell_recommendation(symbol, analysis)
    return jsonify({"speech": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
