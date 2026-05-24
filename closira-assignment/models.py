"""
Data models for the Closira agentic workflow.
Uses Pydantic for validation and structured outputs.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for FAQ responses."""
    HIGH = "HIGH"
    LOW = "LOW"


class FAQResponse(BaseModel):
    """FAQ Agent output model."""
    answer: str = Field(..., description="The answer from SOP")
    confidence: ConfidenceLevel = Field(..., description="HIGH or LOW confidence")
    sop_match: bool = Field(..., description="Whether answer was found in SOP")
    needs_escalation: bool = Field(default=False, description="Whether this should be escalated")


class LeadQualification(BaseModel):
    """Lead qualification data."""
    business_type: Optional[str] = Field(None, description="Type of business")
    team_size: Optional[int] = Field(None, description="Number of team members")
    current_tools: Optional[str] = Field(None, description="Current communication tools")
    lead_quality: str = Field(default="Medium", description="HIGH/Medium/LOW")


class EscalationTrigger(str, Enum):
    """Escalation trigger types."""
    EXPLICIT_REQUEST = "explicit_request"
    COMPLAINT = "complaint"
    OUT_OF_SCOPE = "out_of_scope"
    MULTIPLE_UNANSWERED = "multiple_unanswered"
    MEDICAL_QUESTION = "medical_question"
    PRICING_NEGOTIATION = "pricing_negotiation"
    UNKNOWN = "unknown"


class EscalationDecision(BaseModel):
    """Escalation agent output model."""
    escalated: bool = Field(..., description="Whether to escalate")
    reason: Optional[EscalationTrigger] = Field(None, description="Reason for escalation")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence (0-1)")
    message_to_customer: str = Field(..., description="Message to send to customer")


class ConversationSummary(BaseModel):
    """Final conversation summary from summary agent."""
    customer_intent: str = Field(..., description="Primary intent of the customer")
    key_details: List[str] = Field(default_factory=list, description="Important details from conversation")
    sop_gaps: List[str] = Field(default_factory=list, description="Information not available in SOP")
    sentiment: str = Field(default="NEUTRAL", description="POSITIVE/NEUTRAL/NEGATIVE")
    recommended_next_action: str = Field(..., description="Next action recommendation")
    assigned_to: Optional[str] = Field(None, description="Human agent assignment if applicable")


class ConversationState(BaseModel):
    """Main conversation state object maintained throughout session."""
    messages: List[Dict[str, str]] = Field(default_factory=list, description="Conversation history")
    customer_intent: str = Field(default="", description="Identified customer intent")
    lead_data: LeadQualification = Field(default_factory=LeadQualification, description="Lead qualification data")
    escalated: bool = Field(default=False, description="Whether escalated to human")
    escalation_reason: Optional[EscalationTrigger] = Field(None, description="Reason for escalation")
    escalation_confidence: float = Field(default=0.0, description="Confidence of escalation decision")
    unanswered_count: int = Field(default=0, description="Count of unanswered questions")
    identified_gaps: List[str] = Field(default_factory=list, description="SOP gaps identified")
    created_at: datetime = Field(default_factory=datetime.now, description="Conversation start time")
    summary: Optional[ConversationSummary] = Field(None, description="Final summary if completed")
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EscalationLog(BaseModel):
    """Log entry for escalations."""
    timestamp: datetime = Field(default_factory=datetime.now)
    customer_message: str
    escalation_reason: EscalationTrigger
    confidence: float
    lead_quality: str
    assigned_to_queue: str = Field(default="human_support")
