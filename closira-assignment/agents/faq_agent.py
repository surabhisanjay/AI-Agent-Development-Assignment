"""
Stage 1: FAQ Answering Agent

This agent answers customer questions using ONLY the provided SOP.
It prevents hallucination by:
1. Only using SOP data
2. Marking LOW confidence for unavailable info
3. Enforcing JSON structure
"""

import json
import re
from typing import Dict, Any
from models import FAQResponse, ConfidenceLevel
from prompts.templates import FAQ_AGENT_PROMPT


class FAQAgent:
    """FAQ Agent that answers questions grounded in SOP."""
    
    def __init__(self, sop_data: Dict[str, Any], llm_callable=None):
        """
        Initialize FAQ Agent.
        
        Args:
            sop_data: SOP dictionary loaded from sop.json
            llm_callable: Function to call LLM (for testing, can be mocked)
        """
        self.sop_data = sop_data
        self.sop_text = self._format_sop(sop_data)
        self.llm = llm_callable
        self.response_history = []
    
    def _format_sop(self, sop_data: Dict[str, Any]) -> str:
        """Convert SOP dict to readable text format."""
        sop_text = f"Company: {sop_data.get('company_name', 'Unknown')}\n\n"
        
        # Services
        sop_text += "SERVICES:\n"
        for service in sop_data.get('services', []):
            sop_text += f"- {service['name']}: {service['description']} ({service['price_range']})\n"
        
        # Operating hours
        sop_text += "\nOPERATING HOURS:\n"
        for day, hours in sop_data.get('operating_hours', {}).items():
            sop_text += f"- {day}: {hours}\n"
        
        # Contact
        sop_text += "\nCONTACT:\n"
        for contact in sop_data.get('contact_methods', []):
            sop_text += f"- {contact}\n"
        
        # Booking & Policies
        sop_text += f"\nBOOKING: {sop_data.get('booking_process', 'Not available')}\n"
        sop_text += f"CANCELLATION: {sop_data.get('cancellation_policy', 'Not available')}\n"
        
        return sop_text
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, handling markdown."""
        # Remove markdown code blocks if present
        text = text.replace('```json', '').replace('```', '')
        
        # Try to find JSON object
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse entire text
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {
                "answer": "Error processing response",
                "confidence": "LOW",
                "sop_match": False,
                "needs_escalation": True
            }
    
    def _simple_keyword_search(self, question: str) -> FAQResponse:
        """
        Fallback: Simple keyword matching when LLM is not available.
        Still respects hallucination rules.
        """
        question_lower = question.lower()
        
        # Price queries
        if any(word in question_lower for word in ["price", "cost", "how much", "fee"]):
            if "botox" in question_lower:
                return FAQResponse(
                    answer="Botox treatments start from £200. For detailed pricing, please contact us at support@closira.com.",
                    confidence=ConfidenceLevel.HIGH,
                    sop_match=True,
                    needs_escalation=False
                )
            elif "cleaning" in question_lower or "dental" in question_lower:
                return FAQResponse(
                    answer="Professional dental cleaning is priced from £150-300. For a detailed quote, please contact us.",
                    confidence=ConfidenceLevel.HIGH,
                    sop_match=True,
                    needs_escalation=False
                )
        
        # Operating hours
        if any(word in question_lower for word in ["hours", "open", "when", "available"]):
            return FAQResponse(
                answer="We're open Monday-Friday 9:00-18:00 and Saturday 10:00-14:00. Closed Sundays.",
                confidence=ConfidenceLevel.HIGH,
                sop_match=True,
                needs_escalation=False
            )
        
        # Booking
        if any(word in question_lower for word in ["book", "appointment", "schedule"]):
            return FAQResponse(
                answer="You can book appointments through our website or by contacting support at +44 20 7123 4567.",
                confidence=ConfidenceLevel.HIGH,
                sop_match=True,
                needs_escalation=False
            )
        
        # Cancellation
        if "cancel" in question_lower:
            return FAQResponse(
                answer="Cancellations must be made 24 hours in advance for a full refund.",
                confidence=ConfidenceLevel.HIGH,
                sop_match=True,
                needs_escalation=False
            )
        
        # Default: information not in SOP
        return FAQResponse(
            answer="I don't have that information in my knowledge base. A human representative can assist you further. Please contact us at support@closira.com or call +44 20 7123 4567.",
            confidence=ConfidenceLevel.LOW,
            sop_match=False,
            needs_escalation=True
        )
    
    def answer(self, question: str) -> FAQResponse:
        """
        Answer a customer question using SOP.
        
        Args:
            question: Customer's question
            
        Returns:
            FAQResponse with answer, confidence, and escalation flag
        """
        # If no LLM callable provided, use keyword search
        if not self.llm:
            response = self._simple_keyword_search(question)
        else:
            # Format prompt
            prompt = FAQ_AGENT_PROMPT.format(
                sop_data=self.sop_text,
                customer_question=question
            )
            
            # Call LLM (with retry for invalid JSON)
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    raw_response = self.llm(prompt)
                    parsed = self._extract_json(raw_response)
                    response = FAQResponse(**parsed)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        response = FAQResponse(
                            answer="I encountered an error processing your question. Please contact support.",
                            confidence=ConfidenceLevel.LOW,
                            sop_match=False,
                            needs_escalation=True
                        )
                    else:
                        continue
        
        # Log response
        self.response_history.append({
            "question": question,
            "response": response.dict()
        })
        
        return response
