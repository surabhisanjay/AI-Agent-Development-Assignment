"""
Closira Customer Support Assistant - Main Orchestration

This is the main entry point that orchestrates all 4 agents:
1. FAQ Agent (SOP-grounded QA)
2. Escalation Agent (Safety layer)
3. Lead Qualification Agent
4. Conversation Summary Agent

State is maintained throughout the session via ConversationState.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from models import (
    ConversationState, ConfidenceLevel, LeadQualification, EscalationTrigger
)
from agents.faq_agent import FAQAgent
from agents.escalation_agent import EscalationAgent
from agents.qualification_agent import LeadQualificationAgent, QualificationQuestion
from agents.summary_agent import SummaryAgent


class ClosiraAssistant:
    """Main orchestrator for Closira customer support workflow."""
    
    def __init__(self, sop_path: str = "data/sop.json", llm_callable=None):
        """
        Initialize the Closira Assistant.
        
        Args:
            sop_path: Path to SOP JSON file
            llm_callable: Optional LLM function for advanced features
        """
        
        # Load SOP
        with open(sop_path, 'r') as f:
            self.sop_data = json.load(f)
        
        # Initialize agents
        self.faq_agent = FAQAgent(self.sop_data, llm_callable)
        self.escalation_agent = EscalationAgent(self.sop_data, llm_callable)
        self.qualification_agent = LeadQualificationAgent(llm_callable)
        self.summary_agent = SummaryAgent(llm_callable)
        
        # State management
        self.state = ConversationState()
        
        # Workflow state
        self.current_stage = "faq"  # Stages: faq, qualification, escalation_check, summary
        self.qualification_progress = 0  # 0-3 questions answered
        self.qualification_prompted = False
        self.conversation_log = []
    
    def process_message(self, customer_message: str) -> Dict[str, Any]:
        """
        Main entry point: Process customer message through workflow.
        
        Args:
            customer_message: Customer's input message
            
        Returns:
            Response dict with agent response, next action, etc.
        """
        
        # Add message to state
        self.state.messages.append({
            "role": "customer",
            "content": customer_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # STAGE 1: FAQ ANSWERING
        print("\n[FAQ Agent] Processing question...")
        faq_response = self.faq_agent.answer(customer_message)
        
        self.state.messages.append({
            "role": "assistant",
            "content": faq_response.answer,
            "timestamp": datetime.now().isoformat()
        })
        
        # Track unanswered
        if faq_response.confidence == ConfidenceLevel.LOW:
            self.state.unanswered_count += 1
            self.state.identified_gaps.append(customer_message)
        
        # STAGE 2: ESCALATION CHECK
        print("[Escalation Agent] Checking escalation triggers...")
        escalation_decision = self.escalation_agent.detect_escalation(
            customer_message,
            self.state,
            faq_response.confidence.value
        )
        
        if escalation_decision.escalated:
            print(f"[Escalation] Escalating - Reason: {escalation_decision.reason}")
            self.state.escalated = True
            self.state.escalation_reason = escalation_decision.reason
            self.state.escalation_confidence = escalation_decision.confidence
            self.current_stage = "summary"
            
            # Jump to summary
            return self._finalize_conversation(escalation_decision)
        
        # STAGE 3: LEAD QUALIFICATION (if not escalated)
        customer_message_count = len([m for m in self.state.messages if m['role'] == 'customer'])

        # Delay qualification until the customer has asked a few questions first.
        if self.qualification_progress < 3 and not self.qualification_prompted and customer_message_count >= 5:
            print(f"[Qualification] Prompting new chat after {customer_message_count} customer messages")
            self.qualification_prompted = True
            return {
                "status": "continue",
                "message": (
                    "I’d like to qualify this lead before handing it off. "
                    "Please start a new chat and answer these lead questions:\n"
                    "1) What type of business do you run?\n"
                    "2) How many team members do you have?\n"
                    "3) What tools are you currently using for customer communication?"
                ),
                "next_action": "awaiting_new_chat"
            }

        # First message or waiting for next customer message
        print(f"[FAQ] Returning answer (customer messages so far: {customer_message_count})")
        return {
            "status": "continue",
            "message": faq_response.answer,
            "next_action": "awaiting_customer_response"
        }
    
    def _ask_qualification_question(self) -> Dict[str, Any]:
        """Ask the next qualification question."""
        
        question_num = self.qualification_progress + 1
        question_obj = QualificationQuestion.get_question(question_num)
        
        if not question_obj:
            # All questions asked, move to summary
            self.qualification_progress = 3
            return self.process_message("")  # Trigger summary
        
        question_text = question_obj["question"]
        
        self.state.messages.append({
            "role": "assistant",
            "content": question_text,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "qualification",
            "message": question_text,
            "question_number": question_num,
            "options": question_obj.get("options", []),
            "next_action": "awaiting_qualification_answer"
        }
    
    def answer_qualification_question(self, answer: str) -> Dict[str, Any]:
        """
        Process qualification question answer.
        
        Args:
            answer: Customer's answer to qualification question
            
        Returns:
            Response dict
        """
        
        # Add answer to messages
        self.state.messages.append({
            "role": "customer",
            "content": answer,
            "timestamp": datetime.now().isoformat()
        })
        
        # Store answer
        if self.qualification_progress == 0:
            self.state.lead_data.business_type = answer
        elif self.qualification_progress == 1:
            self.state.lead_data.team_size = self.qualification_agent._extract_team_size(answer)
        elif self.qualification_progress == 2:
            self.state.lead_data.current_tools = answer
        
        self.qualification_progress += 1
        
        # If all 3 questions answered, qualify the lead
        if self.qualification_progress == 3:
            print("[Qualification Agent] All questions answered, qualifying lead...")
            
            qualification = self.qualification_agent.qualify_lead(
                self.state.lead_data.business_type or "",
                answer if self.qualification_progress == 1 else "",
                self.state.lead_data.current_tools or ""
            )
            
            self.state.lead_data.lead_quality = qualification.lead_quality
            
            # Move to summary
            return self._finalize_conversation(None)
        
        # Ask next question
        return self._ask_qualification_question()
    
    def _finalize_conversation(self, escalation_decision=None) -> Dict[str, Any]:
        """
        Finalize conversation with summary.
        
        Args:
            escalation_decision: Optional escalation decision
            
        Returns:
            Final response with summary
        """
        
        print("[Summary Agent] Generating final summary...")
        
        # Generate summary
        summary = self.summary_agent.summarize(self.state)
        self.state.summary = summary
        
        # Format handoff report
        handoff_report = self.summary_agent.format_summary_for_handoff(summary)
        
        # Log escalation if applicable
        if self.state.escalated:
            self._log_escalation()
        
        return {
            "status": "completed",
            "escalated": self.state.escalated,
            "escalation_reason": self.state.escalation_reason.value if self.state.escalation_reason else None,
            "summary": summary.dict(),
            "handoff_report": handoff_report,
            "next_action": "route_to_queue"
        }
    
    def _log_escalation(self):
        """Log escalation to file."""
        
        log_path = Path("logs/escalation_log.json")
        log_path.parent.mkdir(exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "customer_messages": [m["content"] for m in self.state.messages if m["role"] == "customer"],
            "escalation_reason": self.state.escalation_reason.value if self.state.escalation_reason else None,
            "escalation_confidence": self.state.escalation_confidence,
            "lead_quality": self.state.lead_data.lead_quality,
            "unanswered_count": self.state.unanswered_count,
            "assigned_to": self.state.summary.assigned_to if self.state.summary else None
        }
        
        logs = []
        if log_path.exists():
            with open(log_path, 'r') as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        
        with open(log_path, 'w') as f:
            json.dump(logs, f, indent=2)
        
        print(f"[Logging] Escalation logged to {log_path}")
    
    def get_state(self) -> ConversationState:
        """Get current conversation state."""
        return self.state
    
    def reset(self):
        """Reset conversation state for new session."""
        self.state = ConversationState()
        self.current_stage = "faq"
        self.qualification_progress = 0
        self.conversation_log = []
        print("[System] Conversation state reset.")


def run_interactive_session():
    """Run interactive conversation session."""
    
    print("\n" + "="*60)
    print("CLOSIRA CUSTOMER SUPPORT ASSISTANT")
    print("4-Stage Agentic Workflow")
    print("="*60 + "\n")
    
    assistant = ClosiraAssistant()
    
    print("Welcome to Closira support! (Type 'quit' to exit)\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            print("Thank you for contacting Closira. Goodbye!")
            break
        
        if not user_input:
            continue
        
        response = assistant.process_message(user_input)
        
        print(f"\nAssistant: {response.get('message', '')}")
        
        if response.get('status') == 'completed':
            print("\n" + response.get('handoff_report', ''))
            print("\n[System] Conversation completed. Starting new session...\n")
            assistant.reset()
        
        print()


if __name__ == "__main__":
    run_interactive_session()
