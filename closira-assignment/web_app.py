"""
Flask Web Interface for Closira Customer Support Assistant

Provides a modern chat interface with real-time conversation management,
escalation tracking, and lead qualification display.
"""

import json
from flask import Flask, render_template, request, jsonify, session
# from flask_session import Session
from app import ClosiraAssistant
from models import ConversationState
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'closira-secret-key-2026'
Session(app)

# In-memory store for assistant instances per session
assistants = {}


def get_assistant():
    """Get or create assistant for current session."""
    session_id = session.get('session_id', request.remote_addr)
    

    
    if session_id not in assistants:
        assistants[session_id] = ClosiraAssistant()
    
    
    return assistants[session_id]


@app.route('/')
def index():
    """Render main chat interface."""
    return render_template('index.html')


@app.route('/api/message', methods=['POST'])
def send_message():
    """
    Process customer message and return assistant response.
    
    Request JSON:
    {
        "message": "customer message",
        "type": "message|qualification_answer"
    }
    
    Response JSON:
    {
        "status": "continue|qualification|completed",
        "message": "assistant response",
        "question_number": 1|2|3 (if qualification),
        "escalated": bool,
        "escalation_reason": str,
        "lead_quality": str,
        "state": {...}
    }
    """
    
    data = request.json
    message = data.get('message', '').strip()
    message_type = data.get('type', 'message')
    
    if not message:
        return jsonify({
            "error": "Empty message",
            "status": "error"
        }), 400
    
    assistant = get_assistant()
    
    try:
        # Route based on message type
        if message_type == 'qualification_answer':
            response = assistant.answer_qualification_question(message)
        else:
            response = assistant.process_message(message)
        
        state = assistant.get_state()
        
        # Build response
        result = {
            "status": response.get('status', 'continue'),
            "message": response.get('message', ''),
            "escalated": state.escalated,
            "escalation_reason": state.escalation_reason.value if state.escalation_reason else None,
            "lead_quality": state.lead_data.lead_quality if state.lead_data else None,
            "unanswered_count": state.unanswered_count,
            "state": {
                "messages_count": len(state.messages),
                "customer_intent": state.customer_intent,
                "business_type": state.lead_data.business_type,
                "team_size": state.lead_data.team_size,
                "current_tools": state.lead_data.current_tools,
            }
        }
        
        # Add qualification question number if applicable
        if response.get('status') == 'qualification':
            result['question_number'] = response.get('question_number')
        
        # Add handoff report if completed
        if response.get('status') == 'completed':
            result['handoff_report'] = response.get('handoff_report', '')
            result['summary'] = response.get('summary')
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error processing message: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route('/api/state', methods=['GET'])
def get_state():
    """Get current conversation state."""
    assistant = get_assistant()
    state = assistant.get_state()
    
    return jsonify({
        "escalated": state.escalated,
        "escalation_reason": state.escalation_reason.value if state.escalation_reason else None,
        "escalation_confidence": state.escalation_confidence,
        "unanswered_count": state.unanswered_count,
        "message_count": len(state.messages),
        "lead_data": {
            "business_type": state.lead_data.business_type,
            "team_size": state.lead_data.team_size,
            "current_tools": state.lead_data.current_tools,
            "lead_quality": state.lead_data.lead_quality,
        },
        "identified_gaps": state.identified_gaps,
    })


@app.route('/api/conversation', methods=['GET'])
def get_conversation():
    """Get full conversation history."""
    assistant = get_assistant()
    state = assistant.get_state()
    
    return jsonify({
        "messages": state.messages,
        "customer_intent": state.customer_intent,
        "created_at": state.created_at.isoformat(),
    })


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation state for new session."""
    session_id = session.get('session_id', request.remote_addr)
    
    if session_id in assistants:
        del assistants[session_id]
    
    return jsonify({
        "status": "reset",
        "message": "Conversation reset. Starting fresh."
    })


@app.route('/api/escalation-info', methods=['GET'])
def get_escalation_info():
    """Get escalation details."""
    assistant = get_assistant()
    state = assistant.get_state()
    
    if not state.escalated:
        return jsonify({
            "escalated": False,
            "message": "No escalation triggered"
        })
    
    reason_map = {
        "explicit_request": "Customer requested human representative",
        "complaint": "Negative sentiment/complaint detected",
        "out_of_scope": "Question outside knowledge base",
        "multiple_unanswered": "Multiple unanswered questions",
        "medical_question": "Medical/clinical question requires specialist",
        "pricing_negotiation": "Pricing negotiation requires sales team",
    }
    
    queue_map = {
        "explicit_request": "General Support Queue",
        "complaint": "Support Escalation Queue",
        "out_of_scope": "Product Specialists",
        "multiple_unanswered": "Knowledge Specialists",
        "medical_question": "Clinical Specialists",
        "pricing_negotiation": "Sales Team",
    }
    
    reason = state.escalation_reason.value if state.escalation_reason else "unknown"
    
    return jsonify({
        "escalated": True,
        "reason": reason,
        "reason_description": reason_map.get(reason, "Unknown reason"),
        "confidence": state.escalation_confidence,
        "assigned_queue": queue_map.get(reason, "General Queue"),
        "assigned_to": state.summary.assigned_to if state.summary else None,
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "closira-web-interface"})


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    print("\n" + "="*60)
    print("CLOSIRA WEB INTERFACE")
    print("="*60)
    print("\nServer starting at http://localhost:5000")
    print("\nEndpoints:")
    print("  GET  /                    - Chat interface")
    print("  POST /api/message         - Send message")
    print("  GET  /api/state           - Get conversation state")
    print("  GET  /api/conversation    - Get full history")
    print("  GET  /api/escalation-info - Get escalation details")
    print("  POST /api/reset           - Reset conversation")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=5000)
