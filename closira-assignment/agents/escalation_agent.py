"""
Stage 2: Escalation Detection Agent

This agent determines whether a conversation should be escalated to human support.
It checks 6 escalation triggers with confidence scoring.
"""

import re
from typing import Dict, Any, Optional, List
from models import EscalationDecision, EscalationTrigger, ConfidenceLevel, ConversationState
from prompts.templates import ESCALATION_AGENT_PROMPT, SENTIMENT_ANALYSIS_PROMPT


class EscalationAgent:
    """Escalation Detection Agent."""
    
    def __init__(self, sop_data: Dict[str, Any], llm_callable=None):
        """
        Initialize Escalation Agent.
        
        Args:
            sop_data: SOP dictionary
            llm_callable: Function to call LLM
        """
        self.sop_data = sop_data
        self.llm = llm_callable
        self.escalation_log: List[Dict[str, Any]] = []
        
        # Keywords from SOP
        self.escalation_keywords = sop_data.get('escalation_rules', {}).get('keywords', [])
        self.max_unanswered = sop_data.get('escalation_rules', {}).get('max_unanswered_before_escalation', 2)
    
    def _check_explicit_request(self, message: str) -> bool:
        """Check if customer explicitly asks for human."""
        keywords = ["speak to", "human", "agent", "representative", "manager", "talk to someone"]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _check_complaint(self, message: str) -> Optional[float]:
        """
        Check if message contains complaint.
        Returns confidence score (0-1) or None.
        """
        negative_keywords = ["terrible", "awful", "worst", "unhappy", "angry", "disappointed", 
                           "complaint", "issue", "problem", "broken", "failed", "ridiculous"]
        
        count = sum(1 for keyword in negative_keywords if keyword in message.lower())
        
        if count >= 2:
            return 0.95  # High confidence complaint
        elif count == 1:
            return 0.70  # Medium confidence
        else:
            return None  # No complaint
    
    def _check_out_of_scope(self, faq_confidence: str) -> bool:
        """Check if FAQ returned LOW confidence (out of scope)."""
        return faq_confidence == "LOW"
    
    def _check_multiple_unanswered(self, unanswered_count: int) -> bool:
        """Check if >2 questions are unanswered."""
        return unanswered_count > self.max_unanswered
    
    def _check_medical_question(self, message: str) -> bool:
        """Check if message contains medical/health inquiry."""
        medical_keywords = ["medical", "health", "doctor", "clinical", "treatment effect",
                          "side effect", "allergy", "contraindication", "safe", "risk"]
        return any(keyword in message.lower() for keyword in medical_keywords)
    
    def _check_pricing_negotiation(self, message: str) -> bool:
        """Check if customer is negotiating pricing."""
        negotiation_keywords = ["discount", "cheaper", "negotiate", "bulk price", "deal",
                              "special rate", "lower price", "custom quote"]
        return any(keyword in message.lower() for keyword in negotiation_keywords)
    
    def _check_complaint_with_sentiment(self, message: str) -> Optional[float]:
        """
        Use LLM for sentiment analysis if available.
        Falls back to keyword matching.
        """
        if not self.llm:
            return self._check_complaint(message)
        
        try:
            prompt = SENTIMENT_ANALYSIS_PROMPT.format(message=message)
            sentiment = self.llm(prompt).strip().upper()
            
            if sentiment == "NEGATIVE":
                return 0.85
            elif sentiment == "POSITIVE":
                return None
            else:
                # NEUTRAL - no escalation
                return None
        except:
            # Fallback to keyword matching
            return self._check_complaint(message)
    
    def detect_escalation(
        self,
        current_message: str,
        state: ConversationState,
        faq_confidence: str
    ) -> EscalationDecision:
        """
        Detect if conversation should be escalated.
        
        Args:
            current_message: Latest customer message
            state: Current conversation state
            faq_confidence: Confidence from FAQ agent (HIGH/LOW)
            
        Returns:
            EscalationDecision with escalation flag and reason
        """
        
        escalation_reasons = []
        confidence_scores = []
        
        # Trigger 1: Explicit request
        if self._check_explicit_request(current_message):
            escalation_reasons.append(EscalationTrigger.EXPLICIT_REQUEST)
            confidence_scores.append(0.99)
        
        # Trigger 2: Complaint sentiment
        complaint_confidence = self._check_complaint_with_sentiment(current_message)
        if complaint_confidence is not None:
            escalation_reasons.append(EscalationTrigger.COMPLAINT)
            confidence_scores.append(complaint_confidence)
        
        # Trigger 3: Out of scope (LOW FAQ confidence)
        if self._check_out_of_scope(faq_confidence):
            escalation_reasons.append(EscalationTrigger.OUT_OF_SCOPE)
            confidence_scores.append(0.75)
        
        # Trigger 4: Multiple unanswered questions
        if self._check_multiple_unanswered(state.unanswered_count):
            escalation_reasons.append(EscalationTrigger.MULTIPLE_UNANSWERED)
            confidence_scores.append(0.85)
        
        # Trigger 5: Medical question
        if self._check_medical_question(current_message):
            escalation_reasons.append(EscalationTrigger.MEDICAL_QUESTION)
            confidence_scores.append(0.90)
        
        # Trigger 6: Pricing negotiation
        if self._check_pricing_negotiation(current_message):
            escalation_reasons.append(EscalationTrigger.PRICING_NEGOTIATION)
            confidence_scores.append(0.80)
        
        # Decision logic
        if escalation_reasons:
            # Multiple escalation triggers increase confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            primary_reason = escalation_reasons[0]
            
            message = self._get_escalation_message(primary_reason, state)
            
            decision = EscalationDecision(
                escalated=True,
                reason=primary_reason,
                confidence=min(avg_confidence, 0.99),
                message_to_customer=message
            )
        else:
            decision = EscalationDecision(
                escalated=False,
                reason=None,
                confidence=0.0,
                message_to_customer=""
            )
        
        # Log decision
        self.escalation_log.append({
            "timestamp": state.created_at.isoformat(),
            "message": current_message,
            "decision": decision.dict(),
            "triggers_detected": [t.value for t in escalation_reasons]
        })
        
        return decision
    
    def _get_escalation_message(self, reason: EscalationTrigger, state: ConversationState) -> str:
        """Generate appropriate message when escalating."""
        messages = {
            EscalationTrigger.EXPLICIT_REQUEST: 
                "Of course! I'm connecting you with a human representative who can better assist you.",
            
            EscalationTrigger.COMPLAINT:
                "I'm sorry to hear you're experiencing issues. Let me get a specialist to help you right away.",
            
            EscalationTrigger.OUT_OF_SCOPE:
                "This question is outside my current knowledge. I'm connecting you with a specialist who can provide detailed information.",
            
            EscalationTrigger.MULTIPLE_UNANSWERED:
                "I want to make sure you get the right answers. Let me transfer you to a specialist on our team.",
            
            EscalationTrigger.MEDICAL_QUESTION:
                "Medical questions require professional advice. Let me connect you with a clinical specialist.",
            
            EscalationTrigger.PRICING_NEGOTIATION:
                "For custom pricing and special arrangements, I'll connect you with our sales team.",
            
            EscalationTrigger.UNKNOWN:
                "I'm connecting you with a representative who can help further."
        }
        
        return messages.get(reason, "Please hold while I find the right specialist for you.")
