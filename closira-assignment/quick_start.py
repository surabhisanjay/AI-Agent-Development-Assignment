"""
Quick Start Guide - Get up and running in 5 minutes.

This module demonstrates the most common usage patterns.
"""

import json
from app import ClosiraAssistant
from models import ConversationState


def example_1_simple_faq():
    """Example 1: Simple FAQ answering."""
    
    print("="*60)
    print("Example 1: Simple FAQ Question")
    print("="*60)
    
    assistant = ClosiraAssistant()
    
    # Customer asks a simple question
    response = assistant.process_message("What are your operating hours?")
    
    print(f"Question: What are your operating hours?")
    print(f"Answer: {response['message']}")
    
    state = assistant.get_state()
    print(f"Escalated: {state.escalated}")
    print()


def example_2_check_escalation():
    """Example 2: Detect escalation triggers."""
    
    print("="*60)
    print("Example 2: Escalation Detection")
    print("="*60)
    
    assistant = ClosiraAssistant()
    
    # Customer expresses complaint
    response = assistant.process_message(
        "I'm absolutely unhappy with your service!"
    )
    
    state = assistant.get_state()
    
    print(f"Message: I'm absolutely unhappy with your service!")
    print(f"Escalated: {state.escalated}")
    print(f"Reason: {state.escalation_reason.value if state.escalation_reason else 'None'}")
    print(f"Confidence: {state.escalation_confidence:.2%}")
    print()


def example_3_lead_qualification():
    """Example 3: Lead qualification process."""
    
    print("="*60)
    print("Example 3: Lead Qualification")
    print("="*60)
    
    assistant = ClosiraAssistant()
    
    # First message
    response = assistant.process_message("What are your prices?")
    print(f"1. Question: What are your prices?")
    print(f"   Response: {response['message'][:60]}...")
    
    # Qualification questions
    state = assistant.get_state()
    if not state.escalated:
        # Simulate user answers to qualification questions
        response = assistant.answer_qualification_question("Dental clinic")
        print(f"\n2. Q: What type of business do you run?")
        print(f"   A: Dental clinic")
        
        response = assistant.answer_qualification_question("15 people")
        print(f"\n3. Q: How many team members?")
        print(f"   A: 15 people")
        
        response = assistant.answer_qualification_question("WhatsApp and Gmail")
        print(f"\n4. Q: What tools do you use?")
        print(f"   A: WhatsApp and Gmail")
        
        if response['status'] == 'completed':
            state = assistant.get_state()
            print(f"\nLead Quality: {state.lead_data.lead_quality}")
            print(f"Assigned to: {state.summary.assigned_to}")
    print()


def example_4_state_inspection():
    """Example 4: Inspect conversation state."""
    
    print("="*60)
    print("Example 4: Conversation State")
    print("="*60)
    
    assistant = ClosiraAssistant()
    
    assistant.process_message("What's your number?")
    assistant.process_message("Do you take walk-ins?")
    
    state = assistant.get_state()
    
    print(f"Message Count: {len(state.messages)}")
    print(f"Unanswered Questions: {state.unanswered_count}")
    print(f"SOP Gaps Identified: {len(state.identified_gaps)}")
    print(f"Escalated: {state.escalated}")
    
    print(f"\nConversation History:")
    for i, msg in enumerate(state.messages, 1):
        role = msg['role'].upper()
        content = msg['content'][:50]
        print(f"  {i}. [{role}] {content}...")
    print()


def example_5_session_reset():
    """Example 5: Session reset for new conversation."""
    
    print("="*60)
    print("Example 5: Session Reset")
    print("="*60)
    
    assistant = ClosiraAssistant()
    
    print("Session 1:")
    assistant.process_message("What are your hours?")
    state = assistant.get_state()
    print(f"  Message count: {len(state.messages)}")
    
    print("\nResetting...")
    assistant.reset()
    state = assistant.get_state()
    print(f"  Message count after reset: {len(state.messages)}")
    
    print("\nSession 2:")
    assistant.process_message("Do you have parking?")
    state = assistant.get_state()
    print(f"  Message count: {len(state.messages)}")
    print()


def example_6_accessing_sop():
    """Example 6: Access SOP data directly."""
    
    print("="*60)
    print("Example 6: Accessing SOP Data")
    print("="*60)
    
    assistant = ClosiraAssistant()
    
    # Access SOP data
    sop = assistant.sop_data
    
    print("Available Services:")
    for service in sop['services']:
        print(f"  • {service['name']}: {service['price_range']}")
    
    print(f"\nOperating Hours:")
    for day, hours in sop['operating_hours'].items():
        print(f"  • {day}: {hours}")
    print()


def example_7_understanding_escalation_logic():
    """Example 7: Deep dive into escalation logic."""
    
    print("="*60)
    print("Example 7: Escalation Logic Details")
    print("="*60)
    
    assistant = ClosiraAssistant()
    
    test_cases = [
        ("Please connect me to a human", "Explicit Request"),
        ("Terrible service!", "Complaint"),
        ("How long does Botox last?", "Out of Scope"),
        ("Can you negotiate pricing?", "Pricing Negotiation"),
        ("What are the side effects?", "Medical Question"),
    ]
    
    for message, expected_trigger in test_cases:
        response = assistant.process_message(message)
        state = assistant.get_state()
        
        actual_trigger = state.escalation_reason.value if state.escalation_reason else "None"
        
        status = "✓" if actual_trigger == expected_trigger or state.escalated else "○"
        print(f"{status} '{message}'")
        print(f"   Expected: {expected_trigger}")
        print(f"   Actual: {actual_trigger}")
        
        assistant.reset()
    print()


def main():
    """Run all examples."""
    
    print("\n" + "="*60)
    print("CLOSIRA QUICK START GUIDE")
    print("="*60 + "\n")
    
    examples = [
        example_1_simple_faq,
        example_2_check_escalation,
        example_3_lead_qualification,
        example_4_state_inspection,
        example_5_session_reset,
        example_6_accessing_sop,
        example_7_understanding_escalation_logic,
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"Error in {example_func.__name__}: {e}\n")
    
    print("="*60)
    print("Examples Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Run the interactive session: python app.py")
    print("2. Run test scenarios: python test_runner.py")
    print("3. Read documentation: prompt_design.md, README.md")
    print("4. Explore agents in agents/ directory")


if __name__ == "__main__":
    main()
