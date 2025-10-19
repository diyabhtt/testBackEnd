"""
Interactive CLI for testing Alexa queries without an actual Alexa device.
Run this while app.py is running to query the latest analysis.
"""
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from alexa_queries import get_news_summary, get_buy_sell_recommendation, get_detailed_analysis
from chat_sambanova import have_conversation

def load_latest_analysis():
    """Load the latest analysis from the JSON file."""
    filepath = os.path.join(os.path.dirname(__file__), "latest_analysis.json")
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get("symbols", {})
    except Exception as e:
        print(f"Error loading analysis: {e}")
        return None

def parse_symbol(user_input: str) -> str:
    """Extract symbol from user input."""
    symbols_map = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "nvidia": "NVDA",
        "bitcoin": "BTC-USD",
        "btc": "BTC-USD",
        "ethereum": "ETH-USD",
        "eth": "ETH-USD",
        "aapl": "AAPL",
        "msft": "MSFT",
        "nvda": "NVDA"
    }
    
    user_lower = user_input.lower()
    
    for key, symbol in symbols_map.items():
        if key in user_lower:
            return symbol
    
    return None

def handle_query(user_input: str, latest_analysis: dict, conversation_history: list) -> str:
    """Process user query and return response using conversational AI."""
    if not latest_analysis:
        return "⚠️  No data available yet. Please wait for the backend to run at least one cycle."
    
    # Use the LLM for full conversation
    response = have_conversation(conversation_history, latest_analysis, user_input)
    return response

def main():
    """Main interactive loop."""
    print("=" * 70)
    print("🤖 FinGalaxy Interactive CLI - Conversational Mode")
    print("=" * 70)
    print("Have a natural conversation! Ask me anything like:")
    print("  • What's happening with Apple today?")
    print("  • Should I invest in Bitcoin right now?")
    print("  • Compare Apple and Microsoft for me")
    print("  • What's the market sentiment on tech stocks?")
    print("\nType 'exit', 'quit', or 'clear' (to reset conversation) to stop.")
    print("=" * 70 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "bye", "stop"]:
                print("\n👋 Goodbye!")
                break
            
            # Clear conversation history
            if user_input.lower() in ["clear", "reset", "restart"]:
                conversation_history = []
                print("\n🔄 Conversation history cleared.\n")
                continue
            
            # Load latest analysis
            latest_analysis = load_latest_analysis()
            
            # Process query with conversation context
            response = handle_query(user_input, latest_analysis, conversation_history)
            
            # Add to conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
            
            # Keep only last 10 exchanges (20 messages) for context
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            print(f"\n🤖 Assistant: {response}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
