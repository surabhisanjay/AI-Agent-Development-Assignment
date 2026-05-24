"""
Stage 3: Lead Qualification Agent

This agent qualifies leads based on:
1. Business type
2. Team size
3. Current tools usage

Produces lead quality scoring: High/Medium/Low
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from models import LeadQualification


class LeadQualificationAgent:
    """Lead Qualification Agent."""
    
    def __init__(self, llm_callable=None):
        """
        Initialize Lead Qualification Agent.
        
        Args:
            llm_callable: Function to call LLM
        """
        self.llm = llm_callable
        self.qualification_history = []
    
    def _extract_team_size(self, answer: str) -> Optional[int]:
        """Extract numeric team size from free-text or MCQ answer."""
        answer_lower = answer.lower()
        
        if "1-4" in answer_lower or "1 to 4" in answer_lower or "one" in answer_lower and "4" not in answer_lower:
            return 1
        if "5-9" in answer_lower or "5 to 9" in answer_lower or "five" in answer_lower:
            return 5
        if "10-19" in answer_lower or "10 to 19" in answer_lower or "ten" in answer_lower:
            return 10
        if "20" in answer_lower or "+" in answer_lower or "more" in answer_lower:
            return 20
        
        # Look for explicit numbers
        numbers = re.findall(r'\d+', answer)
        if numbers:
            return int(numbers[0])
        
        # Look for text patterns
        if any(word in answer_lower for word in ["solo", "one", "alone", "myself"]):
            return 1
        elif any(word in answer_lower for word in ["small", "few", "couple"]):
            return 3
        elif any(word in answer_lower for word in ["medium", "growing"]):
            return 7
        elif any(word in answer_lower for word in ["large", "big", "team"]):
            return 15
        
        return None
    
    def _score_lead_quality(self, business_type: str, team_size: Optional[int], current_tools: str) -> Tuple[str, str]:
        """
        Score lead quality based on business type, team size, and tools.
        
        Returns:
            Tuple of (lead_quality, reasoning)
        """
        score = 0
        reasoning_points = []
        
        # Team size scoring (most important)
        if team_size is not None:
            if team_size >= 10:
                score += 40
                reasoning_points.append(f"Team size {team_size} (Enterprise)")
            elif team_size >= 5:
                score += 25
                reasoning_points.append(f"Team size {team_size} (Medium)")
            else:
                score += 10
                reasoning_points.append(f"Team size {team_size} (Small)")
        else:
            score += 15
            reasoning_points.append("Team size unclear")
        
        # Current tools scoring (shows pain point)
        tools_lower = current_tools.lower()
        
        if any(tool in tools_lower for tool in ["whatsapp", "email", "sms", "phone"]):
            score += 30
            reasoning_points.append("Using manual communication tools (high opportunity)")
        elif any(tool in tools_lower for tool in ["slack", "teams"]):
            score += 15
            reasoning_points.append("Using basic team tools")
        elif any(tool in tools_lower for tool in ["salesforce", "hubspot", "zendesk"]):
            score += 5
            reasoning_points.append("Already has CRM/automation")
        else:
            score += 20
            reasoning_points.append("Tools unclear")
        
        # Business type scoring
        beauty_dental_keywords = ["dental", "aesthetics", "beauty", "clinic", "medical spa", "salon"]
        if any(keyword in business_type.lower() for keyword in beauty_dental_keywords):
            score += 15
            reasoning_points.append(f"Industry: {business_type} (Perfect fit)")
        else:
            score += 5
            reasoning_points.append(f"Industry: {business_type}")
        
        # Determine quality tier
        if score >= 70:
            quality = "High"
        elif score >= 40:
            quality = "Medium"
        else:
            quality = "Low"
        
        reasoning = "; ".join(reasoning_points)
        return quality, reasoning
    
    def qualify_lead(
        self,
        business_type: str,
        team_size_answer: str,
        current_tools: str
    ) -> LeadQualification:
        """
        Qualify a lead based on responses to 3 questions.
        
        Args:
            business_type: Answer to Q1
            team_size_answer: Answer to Q2
            current_tools: Answer to Q3
            
        Returns:
            LeadQualification object with quality scoring
        """
        
        # Extract numeric team size
        team_size_numeric = self._extract_team_size(team_size_answer)
        
        # Score lead
        lead_quality, reasoning = self._score_lead_quality(
            business_type,
            team_size_numeric,
            current_tools
        )
        
        # Create qualification object
        qualification = LeadQualification(
            business_type=business_type,
            team_size=team_size_numeric,
            current_tools=current_tools,
            lead_quality=lead_quality
        )
        
        # Log
        self.qualification_history.append({
            "business_type": business_type,
            "team_size_raw": team_size_answer,
            "team_size_extracted": team_size_numeric,
            "current_tools": current_tools,
            "lead_quality": lead_quality,
            "reasoning": reasoning,
            "qualification": qualification.dict()
        })
        
        return qualification
    
    def get_qualification_message(self, qualification: LeadQualification) -> str:
        """
        Generate a personalized message based on lead quality.
        """
        
        messages = {
            "High": f"Thank you for sharing these details! Based on your {qualification.business_type} with {qualification.team_size} team members, we can see significant opportunity. Our sales team will reach out with a customized proposal.",
            
            "Medium": f"Thanks for that information. We'd love to show you how we can improve your customer communication. A specialist will be in touch soon.",
            
            "Low": "Thank you for your interest. We'll have someone reach out to discuss how we can help your business."
        }
        
        return messages.get(qualification.lead_quality, "Thank you for your information.")


class QualificationQuestion:
    """Helper class for qualification questions."""
    
    QUESTIONS = [
        {
            "id": 1,
            "question": "What type of business do you run?",
            "key": "business_type",
            "options": [
                "Dental clinic",
                "Aesthetics clinic",
                "Beauty salon",
                "Medical spa",
                "Other"
            ]
        },
        {
            "id": 2,
            "question": "How many team members do you have?",
            "key": "team_size",
            "options": [
                "1-4",
                "5-9",
                "10-19",
                "20+"
            ]
        },
        {
            "id": 3,
            "question": "What tools are you currently using for customer communication?",
            "key": "current_tools",
            "options": [
                "WhatsApp / email",
                "Slack / Teams",
                "Salesforce / HubSpot / Zendesk",
                "No formal tools"
            ]
        }
    ]
    
    @classmethod
    def get_question(cls, question_number: int) -> Dict[str, Any]:
        """Get a qualification question by number (1-3)."""
        if 1 <= question_number <= 3:
            return cls.QUESTIONS[question_number - 1]
        return None
    
    @classmethod
    def get_all_questions(cls) -> list:
        """Get all qualification questions."""
        return cls.QUESTIONS
