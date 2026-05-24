#!/bin/bash
# Startup script for Closira Web Interface

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       CLOSIRA CUSTOMER SUPPORT WEB INTERFACE               ║"
echo "║       4-Stage Agentic Workflow with State Management       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Create logs directory
mkdir -p logs

# Start the Flask app
echo ""
echo "✅ Starting Closira Web Interface..."
echo ""
echo "🌐 Access the interface at: http://localhost:5000"
echo "📖 API endpoints:"
echo "   POST /api/message          - Send customer message"
echo "   GET  /api/state            - Get conversation state"
echo "   GET  /api/escalation-info  - Get escalation details"
echo "   POST /api/reset            - Reset conversation"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python web_app.py
