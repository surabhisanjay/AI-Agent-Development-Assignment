"""
Stage 4: Conversation Summary Agent

This agent generates a structured summary of the entire conversation
for human handoff, escalation reports, or archival.
"""

import json
import re
from typing import Dict, Any, List
from models import ConversationSummary, ConversationState
from prompts.templates import SUMMARY_AGENT_PROMPT, SENTIMENT_ANALYSIS_PROMPT


class SummaryAgent:
    """Conversation Summary Agent."""
    
    def __init__(self, llm_callable=None):
        """
        Initialize Summary Agent.
        
        Args:
            llm_callable: Function to call LLM
        """
        self.llm = llm_callable
        self.summary_history = []
    
    def _format_conversation_for_summary(self, state: ConversationState) -> str:
        """Format conversation history as readable text."""
        formatted = "CONVERSATION HISTORY:\n"
        formatted += "-" * 50 + "\n"
        
        for i, msg in enumerate(state.messages, 1):
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            formatted += f"{i}. {role}: {content}\n"
        
        return formatted
    
    def _extract_key_details(self, state: ConversationState) -> List[str]:
        """Extract key business details from conversation."""
        details = []
        
        # Add lead data
        if state.lead_data.business_type:
            details.append(f"Business: {state.lead_data.business_type}")
        if state.lead_data.team_size:
            details.append(f"Team Size: {state.lead_data.team_size} members")
        if state.lead_data.current_tools:
            details.append(f"Current Tools: {state.lead_data.current_tools}")
        if state.lead_data.lead_quality:
            details.append(f"Lead Quality: {state.lead_data.lead_quality}")
        
        # Extract from conversation
        messages_text = " ".join([msg.get("content", "") for msg in state.messages])
        
        if "schedule" in messages_text.lower() or "book" in messages_text.lower():
            details.append("Interested in scheduling consultation")
        
        if "price" in messages_text.lower() or "cost" in messages_text.lower():
            details.append("Asked about pricing")
        
        return details
    
    def _identify_sop_gaps(self, state: ConversationState) -> List[str]:
        """Identify information not available in SOP."""
        gaps = state.identified_gaps.copy()
        
        # Additional gap detection from messages
        messages_text = " ".join([msg.get("content", "") for msg in state.messages])
        messages_lower = messages_text.lower()
        
        gap_keywords = {
            "duration": ["how long", "lasts", "duration", "recovery time"],
            "side effects": ["side effect", "reaction", "complications", "risk"],
            "qualification": ["requirements", "prerequisites", "eligible", "suitable"],
            "timing": ["how soon", "available", "appointment", "wait time"]
        }
        
        for gap_type, keywords in gap_keywords.items():
            if any(kw in messages_lower for kw in keywords) and gap_type not in gaps:
                gaps.append(f"Information about {gap_type} not available in SOP")
        
        return gaps
    
    def _analyze_sentiment_simple(self, state: ConversationState) -> str:
        """Simple sentiment analysis from conversation."""
        messages_text = " ".join([msg.get("content", "") for msg in state.messages])
        messages_lower = messages_text.lower()
        
        positive_words = ["great", "excellent", "love", "happy", "thank", "appreciate", "perfect"]
        negative_words = ["terrible", "awful", "worst", "unhappy", "angry", "complaint", "disappointed"]
        
        pos_count = sum(1 for word in positive_words if word in messages_lower)
        neg_count = sum(1 for word in negative_words if word in messages_lower)
        
        if neg_count > pos_count:
            return "NEGATIVE"
        elif pos_count > 0:
            return "POSITIVE"
        else:
            return "NEUTRAL"
    
    def _get_recommended_action(
        self,
        customer_intent: str,
        escalated: bool,
        escalation_reason: Any,
        lead_quality: str
    ) -> str:
        """Generate recommended next action."""
        
        if escalated:
            reason_map = {
                "explicit_request": "Create support ticket and assign to available representative",
                "complaint": "Escalate to senior support specialist with emphasis on resolution",
                "out_of_scope": "Route to product specialist for detailed information",
                "multiple_unanswered": "Assign to knowledge specialist",
                "medical_question": "Route to clinical specialist for medical guidance",
                "pricing_negotiation": "Assign to sales representative for custom quote",
                "unknown": "Create general support ticket"
            }
            
            reason_str = escalation_reason.value if hasattr(escalation_reason, 'value') else str(escalation_reason)
            return reason_map.get(reason_str, "Create support ticket")
        
        # Non-escalated recommendations
        if "pricing" in customer_intent.lower() or "booking" in customer_intent.lower():
            if lead_quality == "High":
                return "Schedule sales call to discuss custom packages"
            else:
                return "Send pricing information and follow up in 3 days"
        
        elif "information" in customer_intent.lower():
            return "Send FAQ document and offer scheduling consultation"
        
        else:
            return "Create contact record and await next customer message"
    
    def summarize(self, state: ConversationState) -> ConversationSummary:
        """
        Generate comprehensive conversation summary.
        
        Args:
            state: Current conversation state
            
        Returns:
            ConversationSummary object
        """
        
        # Extract components
        key_details = self._extract_key_details(state)
        sop_gaps = self._identify_sop_gaps(state)
        sentiment = self._analyze_sentiment_simple(state)
        
        # Determine customer intent
        customer_intent = state.customer_intent or self._infer_intent(state)
        
        # Get recommended action
        recommended_action = self._get_recommended_action(
            customer_intent,
            state.escalated,
            state.escalation_reason,
            state.lead_data.lead_quality
        )
        
        # Determine assignment
        assigned_to = self._determine_assignment(
            state.escalation_reason,
            state.lead_data.lead_quality
        )
        
        # Create summary
        summary = ConversationSummary(
            customer_intent=customer_intent,
            key_details=key_details,
            sop_gaps=sop_gaps,
            sentiment=sentiment,
            recommended_next_action=recommended_action,
            assigned_to=assigned_to
        )
        
        # Log
        self.summary_history.append({
            "timestamp": state.created_at.isoformat(),
            "summary": summary.dict()
        })
        
        return summary
    
    def _infer_intent(self, state: ConversationState) -> str:
        """Infer customer intent from messages if not explicitly set."""
        
        if not state.messages:
            return "Unknown"
        
        # Look at first message
        first_msg = state.messages[0].get("content", "").lower()
        
        if any(word in first_msg for word in ["price", "cost", "how much"]):
            return "Pricing inquiry"
        elif any(word in first_msg for word in ["book", "schedule", "appointment"]):
            return "Booking consultation"
        elif any(word in first_msg for word in ["how", "what", "tell"]):
            return "General information request"
        elif any(word in first_msg for word in ["problem", "issue", "complaint"]):
            return "Support request"
        else:
            return "General inquiry"
    
    def _determine_assignment(self, escalation_reason: Any, lead_quality: str) -> str:
        """Determine which queue/team to assign."""
        
        if escalation_reason:
            reason_str = escalation_reason.value if hasattr(escalation_reason, 'value') else str(escalation_reason)
            
            mapping = {
                "complaint": "Support Escalation Queue",
                "medical_question": "Clinical Specialists",
                "pricing_negotiation": "Sales Team",
                "explicit_request": "General Support Queue",
                "out_of_scope": "Product Specialists",
                "multiple_unanswered": "Knowledge Specialists"
            }
            
            return mapping.get(reason_str, "General Support Queue")
        
        # Non-escalated assignment based on lead quality
        if lead_quality == "High":
            return "Sales Development Team"
        elif lead_quality == "Medium":
            return "Lead Nurture Queue"
        else:
            return "General Inquiry Queue"
    
    def format_summary_for_handoff(self, summary: ConversationSummary) -> str:
        """Format summary as human-readable text for agent handoff."""
        
        output = "\n" + "=" * 60 + "\n"
        output += "CONVERSATION SUMMARY REPORT\n"
        output += "=" * 60 + "\n\n"
        
        output += f"CUSTOMER INTENT:\n{summary.customer_intent}\n\n"
        
        output += "KEY DETAILS:\n"
        for detail in summary.key_details:
            output += f"  • {detail}\n"
        output += "\n"
        
        output += f"SENTIMENT: {summary.sentiment}\n\n"
        
        if summary.sop_gaps:
            output += "SOP GAPS (Information Not Available):\n"
            for gap in summary.sop_gaps:
                output += f"  • {gap}\n"
            output += "\n"
        
        output += f"RECOMMENDED NEXT ACTION:\n{summary.recommended_next_action}\n\n"
        
        if summary.assigned_to:
            output += f"ASSIGN TO: {summary.assigned_to}\n"
        
        output += "=" * 60 + "\n"
        
        return output
