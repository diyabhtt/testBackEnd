#!/bin/bash

# Check for Python 3
if command -v python3 &> /dev/null; then
    echo "🚀 Starting FinGalaxy Backend..."
    python3 app.py
elif command -v python &> /dev/null; then
    echo "🚀 Starting FinGalaxy Backend..."
    python app.py
else
    echo "❌ Error: Python not found. Please install Python 3."
    exit 1
fi
