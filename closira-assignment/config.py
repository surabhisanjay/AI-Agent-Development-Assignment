"""
Configuration file for Closira Assistant.

Customize escalation thresholds, timeouts, and other settings here.
"""

# Escalation Settings
ESCALATION_CONFIG = {
    "max_unanswered_before_escalation": 2,
    "min_escalation_confidence": 0.5,
    
    # Trigger configurations
    "triggers": {
        "explicit_request": {
            "enabled": True,
            "keywords": ["speak to", "human", "agent", "representative", "manager"],
            "confidence": 0.99
        },
        "complaint": {
            "enabled": True,
            "keywords": ["terrible", "awful", "worst", "unhappy", "angry", "disappointed"],
            "min_count_for_escalation": 1,
            "base_confidence": 0.85
        },
        "out_of_scope": {
            "enabled": True,
            "faq_confidence_threshold": "LOW",
            "confidence": 0.75
        },
        "multiple_unanswered": {
            "enabled": True,
            "threshold": 2,
            "confidence": 0.85
        },
        "medical_question": {
            "enabled": True,
            "keywords": ["medical", "health", "doctor", "clinical", "side effect", "allergy"],
            "confidence": 0.90
        },
        "pricing_negotiation": {
            "enabled": True,
            "keywords": ["discount", "cheaper", "bulk", "negotiate", "deal", "custom"],
            "confidence": 0.80
        }
    }
}

# Lead Qualification Settings
QUALIFICATION_CONFIG = {
    "scoring": {
        "team_size": {
            "weights": {
                "enterprise": {"min": 10, "points": 40},
                "smb": {"min": 5, "max": 9, "points": 25},
                "solo": {"min": 0, "max": 4, "points": 10}
            }
        },
        "tools": {
            "weights": {
                "manual": {"keywords": ["whatsapp", "email", "sms", "phone"], "points": 30},
                "basic": {"keywords": ["slack", "teams"], "points": 15},
                "advanced": {"keywords": ["salesforce", "hubspot", "zendesk"], "points": 5}
            }
        },
        "industry": {
            "weights": {
                "fit": {"keywords": ["dental", "aesthetics", "beauty", "clinic", "spa"], "points": 15},
                "other": {"points": 5}
            }
        }
    },
    "tiers": {
        "high": {"min_score": 70},
        "medium": {"min_score": 40, "max_score": 69},
        "low": {"max_score": 39}
    }
}

# API Settings (for future OpenAI integration)
API_CONFIG = {
    "provider": "openai",  # Can be "openai", "anthropic", etc.
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 500,
    "timeout": 10,
}

# Logging Settings
LOGGING_CONFIG = {
    "escalation_log_path": "logs/escalation_log.json",
    "conversation_log_path": "logs/conversation_log.json",
    "log_level": "INFO",
    "archive_on_complete": True
}

# Conversation Settings
CONVERSATION_CONFIG = {
    "max_message_history": 100,
    "session_timeout_minutes": 30,
    "enable_sentiment_analysis": True,
    "sentiment_method": "keyword",  # "keyword" or "llm"
}

# UI/Formatting Settings
UI_CONFIG = {
    "show_confidence_scores": True,
    "show_escalation_details": True,
    "format_json_output": True,
    "verbose_mode": False
}
