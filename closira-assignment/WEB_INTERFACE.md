# Closira Web Interface - User Guide

## Quick Start

### 1. Start the Web Server

```bash
cd /Users/chandrikasanjay/dl_lab/closira-assignment

# Option A: Using the startup script (recommended)
chmod +x run_web.sh
./run_web.sh

# Option B: Manual startup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python web_app.py
```

### 2. Open in Browser

Navigate to: **http://localhost:5000**

---

## Interface Overview

### Main Chat Area
- **Left Column**: Real-time conversation with the Closira assistant
- **Right Sidebar**: Conversation metadata and lead information

### Sidebar Sections

#### Conversation Info
- **Status**: Shows if conversation is active or escalated
- **Messages**: Total count of messages exchanged
- **Unanswered**: Count of unanswered questions

#### Lead Data
- **Business Type**: Customer's business category
- **Team Size**: Number of employees
- **Tools**: Current communication tools used
- **Lead Quality**: Qualification score (High/Medium/Low)

#### Escalation Info (if applicable)
- **Reason**: Why the conversation was escalated
- **Confidence**: Escalation confidence score (0-100%)
- **Queue**: Which team the customer is assigned to

---

## Features

### 1. Real-Time Chat
- Type your message and press Enter or click Send
- Responses appear instantly
- Full conversation history maintained

### 2. Lead Qualification
- After initial message, you'll be asked 3 qualification questions:
  1. What type of business do you run?
  2. How many team members do you have?
  3. What communication tools do you use?
- Qualification indicator shows progress (Q 1 of 3)

### 3. Escalation Detection
- System automatically detects escalation triggers:
  - Explicit request for human
  - Complaint/negative sentiment
  - Out-of-scope questions
  - Medical inquiries
  - Pricing negotiations
  - Multiple unanswered questions
- If escalated, sidebar shows escalation details

### 4. Conversation Statistics
- Click "📊 Stats" button to view:
  - Message count
  - Unanswered questions
  - Lead information
  - Conversation flow
  - Business metrics

### 5. New Chat
- Click "🔄 New Chat" to start a fresh conversation
- Confirmation prompt prevents accidental resets

---

## How It Works

### Stage 1: FAQ Answering
- Answer questions from the knowledge base (SOP)
- Marked with confidence (HIGH/LOW)
- Low confidence triggers escalation consideration

### Stage 2: Escalation Detection
- **6 Escalation Triggers**:
  1. **Explicit Request** - "speak to human" (confidence: 0.99)
  2. **Complaint** - Negative sentiment (confidence: 0.70-0.95)
  3. **Out-of-Scope** - SOP doesn't have answer (confidence: 0.75)
  4. **Multiple Unanswered** - >2 questions can't be answered (confidence: 0.85)
  5. **Medical Question** - Health/clinical inquiry (confidence: 0.90)
  6. **Pricing Negotiation** - Custom pricing request (confidence: 0.80)

### Stage 3: Lead Qualification
- 3 predefined questions asked
- Lead scored as High/Medium/Low based on:
  - Team size (≥10 = High)
  - Tools used (manual tools = high opportunity)
  - Industry fit (beauty/dental = bonus)

### Stage 4: Conversation Summary
- When conversation completes:
  - Customer intent extracted
  - Key details collected
  - SOP gaps identified
  - Next actions recommended
  - Assigned to appropriate queue

---

## API Endpoints

### Send Message
```bash
POST /api/message
Content-Type: application/json

{
  "message": "What are your prices?",
  "type": "message"  # or "qualification_answer"
}

Response:
{
  "status": "continue|qualification|completed|error",
  "message": "Assistant response",
  "escalated": boolean,
  "lead_quality": "High|Medium|Low|null",
  "state": {...}
}
```

### Get State
```bash
GET /api/state

Response:
{
  "escalated": boolean,
  "escalation_reason": "trigger_type",
  "escalation_confidence": 0.75,
  "message_count": 5,
  "unanswered_count": 1,
  "lead_data": {
    "business_type": "Dental clinic",
    "team_size": 8,
    "current_tools": "WhatsApp",
    "lead_quality": "Medium"
  }
}
```

### Get Escalation Info
```bash
GET /api/escalation-info

Response (if escalated):
{
  "escalated": true,
  "reason": "complaint",
  "reason_description": "Negative sentiment detected",
  "confidence": 0.92,
  "assigned_queue": "Support Escalation Queue"
}
```

### Get Conversation History
```bash
GET /api/conversation

Response:
{
  "messages": [
    {"role": "customer", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "customer_intent": "Pricing inquiry",
  "created_at": "2024-05-24T10:30:00"
}
```

### Reset Conversation
```bash
POST /api/reset

Response:
{
  "status": "reset",
  "message": "Conversation reset. Starting fresh."
}
```

---

## Example Conversations

### Example 1: Standard Q&A
```
Customer: "What are your Botox prices?"
Assistant: "Botox treatments start from £200..."
Assistant (Q1): "What type of business do you run?"
Customer: "Dental clinic"
Assistant (Q2): "How many team members do you have?"
Customer: "15"
Assistant (Q3): "What tools do you use for communication?"
Customer: "WhatsApp and email"
[Conversation completed - assigned to Lead Nurture Queue]
```

### Example 2: Escalation
```
Customer: "Your service is terrible!"
[System detects: complaint, confidence 0.92]
[Sidebar shows escalation: Support Escalation Queue]
[Conversation summary prepared]
```

### Example 3: Medical Question
```
Customer: "What are the side effects of Botox?"
Assistant: "I don't have medical information in my knowledge base."
[System detects: out_of_scope + medical_question]
[Escalated to Clinical Specialists]
```

---

## Troubleshooting

### Port 5000 Already in Use
```bash
# Use a different port
python web_app.py --port 5001
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Flask Not Starting
```bash
# Install Flask manually
pip install flask flask-session
```

### Missing Logs Directory
```bash
# Create it manually
mkdir -p logs
```

---

## Customization

### Change Port
Edit `web_app.py`, change the last line:
```python
app.run(debug=True, port=8000)  # Change 5000 to your preferred port
```

### Modify UI Theme
Edit `static/css/style.css` to customize:
- Colors (`:root` variables)
- Font sizes
- Layout
- Animations

### Add Custom UI Elements
Edit `templates/index.html` to add:
- New sidebar sections
- Chat bubbles
- Modal windows
- Status indicators

---

## Performance

- **Response Time**: <1 second (with fallback) / <3 seconds (with LLM)
- **Concurrent Users**: Supports multiple concurrent sessions
- **Session Persistence**: Sessions stored in `flask_session/` directory
- **Database**: Optional (currently in-memory storage)

---

## Security Notes

- Change `app.secret_key` in `web_app.py` before production
- Sessions stored locally (filesystem)
- No authentication implemented (add if needed)
- Input validation on all endpoints

---

## Next Steps

1. **Run the interface**: `./run_web.sh`
2. **Start a conversation**: Type your message
3. **Explore escalation**: Try different triggers
4. **View stats**: Click the Stats button
5. **Review logs**: Check `logs/escalation_log.json`

---

## Support

For issues or questions:
1. Check the main [README.md](README.md)
2. Review [prompt_design.md](prompt_design.md)
3. See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
4. Run `test_runner.py` for examples

---

**Version**: 1.0  
**Last Updated**: May 24, 2026
