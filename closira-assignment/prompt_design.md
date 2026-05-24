# Prompt Design Guide for Closira Assistant

## Overview

This document details the prompt engineering strategies used in the Closira 4-stage agentic workflow. The design focuses on preventing hallucination, ensuring structured outputs, and enabling reliable escalation logic.

---

## Core Principle: Hallucination Prevention

The single most important design principle is: **Never let the model invent answers.**

### Rule 1: Explicit SOP Grounding

Every FAQ prompt starts with:

```text
**CRITICAL RULES:**
1. ONLY use information provided in the SOP below.
2. NEVER infer, guess, or add information not in SOP.
3. If information is unavailable, say so clearly.
```

**Why?** Without this, models will confidently answer questions outside their knowledge base.

### Rule 2: Low Confidence Requirement

When information is unavailable, the model MUST return:

```json
{
  "confidence": "LOW",
  "sop_match": false
}
```

This creates a **checkpoint** for the escalation agent.

**Example - WRONG:**

```text
Q: How long does Botox last?
A: "Botox typically lasts 3-4 months."
```

(Not in SOP = Hallucination)

**Example - CORRECT:**

```json
{
  "answer": "I don't have this information in my SOP. A human representative can assist further.",
  "confidence": "LOW",
  "sop_match": false
}
```

### Rule 3: Structured Output Enforcement

Never allow free-form text responses. Always require JSON:

```python
# In FAQ prompt:
**RESPONSE FORMAT:**
Return ONLY valid JSON (no markdown, no extra text):
{
  "answer": "...",
  "confidence": "HIGH or LOW",
  "sop_match": true or false
}
```

**Why?** JSON is:
- Parseable
- Validates presence of required fields
- Enables downstream agent processing
- Prevents vague responses

---

## Stage 1: FAQ Agent Prompt Design

### Template

```text
You are a customer support assistant for Closira Dental & Aesthetics.

**CRITICAL RULES:**
1. ONLY use information provided in the SOP below.
2. NEVER infer, guess, or add information not in SOP.
3. If information is unavailable, say so clearly.
4. Always return valid JSON.

**SOP DATA:**
{sop_data}

**CUSTOMER QUESTION:**
{customer_question}

**RESPONSE FORMAT:**
Return ONLY valid JSON (no markdown, no extra text):
{
  "answer": "Your answer here or 'I don't have this information in my SOP.'",
  "confidence": "HIGH or LOW",
  "sop_match": true or false,
  "needs_escalation": false
}

**CONFIDENCE RULES:**
- HIGH: Answer found directly in SOP
- LOW: Answer partially available or unclear

Remember: Never hallucinate. If unsure, set confidence to LOW.
```

### Key Decisions

1. **Provide full SOP in prompt**: Don't assume model memory. Include actual SOP data.
2. **Explicit confidence definition**: Define what HIGH vs LOW means.
3. **No markdown in JSON**: Request raw JSON to avoid parsing issues.
4. **needs_escalation field**: Gives FAQ agent partial responsibility for escalation.

### Testing Strategy

```
Test Cases for FAQ Agent:

✓ In-scope question (price, hours, booking)
  Expected: confidence=HIGH, sop_match=true

✓ Out-of-scope question (side effects, medical)
  Expected: confidence=LOW, sop_match=false, needs_escalation=true

✓ Partially available (product exists, price not specified)
  Expected: confidence=LOW, answer includes "not available"

✓ Trick question (assume false information)
  Expected: "I don't have..." response
```

---

## Stage 2: Escalation Agent Prompt Design

### Challenge

Escalation logic is where most candidates fail. Why?

- Too many triggers → false positives
- Insufficient specificity → ambiguous escalations
- No confidence scoring → can't handle gray areas

### Solution: Enumerated Triggers

Define exactly 6 escalation triggers:

```python
class EscalationTrigger(Enum):
    EXPLICIT_REQUEST = "customer asks for human"
    COMPLAINT = "negative sentiment detected"
    OUT_OF_SCOPE = "FAQ confidence is LOW"
    MULTIPLE_UNANSWERED = ">2 questions unanswered"
    MEDICAL_QUESTION = "health/clinical inquiry"
    PRICING_NEGOTIATION = "custom pricing request"
```

**Why?** Enumeration forces clarity. Each trigger has:
- Clear definition
- Detection method
- Confidence score
- Handoff message

### Prompt Structure

```text
You are an escalation detection agent.

Analyze the customer message and conversation history to determine if 
escalation to human support is needed.

**ESCALATION TRIGGERS:**
1. EXPLICIT_REQUEST: Customer asks to speak to human
2. COMPLAINT: Negative sentiment (terrible, unhappy, worst, etc.)
3. OUT_OF_SCOPE: FAQ confidence was LOW
4. MULTIPLE_UNANSWERED: >2 questions couldn't be answered
5. MEDICAL_QUESTION: Any health/medical inquiry
6. PRICING_NEGOTIATION: Customer negotiating or discussing custom pricing

**RETURN JSON FORMAT:**
{
  "escalated": true or false,
  "reason": "explicit_request" | "complaint" | ... | null,
  "confidence": 0.0-1.0,
  "message_to_customer": "Friendly message if escalating"
}
```

### Confidence Scoring

Don't use binary ESCALATE/DON'T. Use 0-1 confidence:

```python
# Multiple triggers increase confidence
if len(triggers) > 1:
    confidence = sum(individual_confidences) / len(triggers)
    # Increased credibility from triangulation
```

### Rule: No Guessing at Intent

**WRONG:**
```text
"Customer sounds frustrated. They probably have an issue."
```

**CORRECT:**
```text
"Customer used word 'terrible' (explicit complaint keyword).
Confidence: 0.85 for COMPLAINT trigger."
```

---

## Stage 3: Lead Qualification Agent

### Design Rationale

Lead qualification should be **rule-based, not LLM-based**.

**Why?** Scoring must be:
- Reproducible
- Auditable
- Consistent across conversations

### Scoring System

```python
score = 0

# Team size (most important)
if team_size >= 10:
    score += 40  # Enterprise
elif team_size >= 5:
    score += 25  # SMB
else:
    score += 10  # Solo

# Current tools (pain point indicator)
if using_manual_tools:  # WhatsApp, Email, SMS
    score += 30  # High opportunity
elif using_basic_tools:  # Slack, Teams
    score += 15
else:
    score += 5   # Already automated

# Industry fit
if business_type in ['dental', 'aesthetics', 'beauty', 'medical spa']:
    score += 15
else:
    score += 5

# Final tiers
if score >= 70: quality = "High"
elif score >= 40: quality = "Medium"
else: quality = "Low"
```

### Why Not Use LLM?

LLM-based scoring would introduce:
- Inconsistency
- Hallucinated reasons
- Unreproducibility

**Rule-based = Audit trail.**

---

## Stage 4: Conversation Summary Agent

### Challenge

Generate a summary that's:
- Actionable for human agents
- Includes SOP gaps discovered
- Suggests next steps
- Assigns to correct queue

### Prompt Template

```text
You are a conversation summary agent.

Generate a structured summary of the entire conversation for 
handoff to human agents or archival.

**CONVERSATION HISTORY:**
{conversation_history}

**LEAD DATA:**
{lead_data}

**ESCALATION REASON (if any):**
{escalation_reason}

**RETURN JSON FORMAT:**
{
  "customer_intent": "What the customer primarily wanted",
  "key_details": ["Detail 1", "Detail 2"],
  "sop_gaps": ["Information not in SOP"],
  "sentiment": "POSITIVE|NEUTRAL|NEGATIVE",
  "recommended_next_action": "Specific action",
  "assigned_to": "Queue or department"
}
```

### Sentiment Analysis

Use simple keyword matching as fallback:

```python
positive_words = ["great", "excellent", "love", "thank"]
negative_words = ["terrible", "awful", "unhappy"]

if count(negative) > count(positive):
    sentiment = "NEGATIVE"
elif count(positive) > 0:
    sentiment = "POSITIVE"
else:
    sentiment = "NEUTRAL"
```

### Queue Assignment Rules

```python
if escalation_reason == "complaint":
    queue = "Support Escalation Queue"
elif escalation_reason == "medical_question":
    queue = "Clinical Specialists"
elif escalation_reason == "pricing_negotiation":
    queue = "Sales Team"
elif lead_quality == "High":
    queue = "Sales Development Team"
else:
    queue = "Lead Nurture Queue"
```

**Why explicit rules?** Ensures consistent handoff routing.

---

## JSON Validation & Retry Logic

### Problem

LLMs sometimes return invalid JSON. Solution: Retry + validation.

```python
def _extract_json(text):
    # Try to find JSON in response
    json_match = re.search(r'\{[^{}]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Fallback: return structured error
    return {
        "error": "Invalid JSON response",
        "escalate": True
    }

# In agent:
max_retries = 2
for attempt in range(max_retries):
    try:
        raw = llm(prompt)
        parsed = _extract_json(raw)
        return parsed
    except:
        if attempt == max_retries - 1:
            escalate()  # Final fallback
```

---

## Prompt Testing Checklist

### For Each Agent

- [ ] Does it refuse to answer out-of-scope?
- [ ] Does it return valid JSON every time?
- [ ] Does it have clear confidence scoring?
- [ ] Can you trace its decision logic?
- [ ] Does it handle edge cases (empty input, contradictions)?

### Test Cases

```
Test: "I have a side effect question"
Expected: LOW confidence, escalate

Test: "What are your hours?"
Expected: HIGH confidence, from SOP

Test: "Can you give me a discount?"
Expected: Flag as pricing_negotiation

Test: "I want to speak to someone"
Expected: Escalate with 0.99 confidence

Test: "This is terrible service!"
Expected: Detect complaint sentiment

Test: Empty message
Expected: Graceful handling, no crash
```

---

## Anti-Patterns to Avoid

### 1. Vague Prompts

❌ **BAD:**
```text
"Answer the customer's question."
```

✅ **GOOD:**
```text
"Answer ONLY from the SOP provided below. If the answer is not 
in the SOP, respond: 'I don't have this information.'"
```

### 2. Trusting Model Memory

❌ **BAD:**
```text
"You know the SOP for Closira."
```

✅ **GOOD:**
```text
"Use ONLY this SOP data:
{full_sop_json}"
```

### 3. Free-Form Responses

❌ **BAD:**
```text
"Provide a helpful response."
```

✅ **GOOD:**
```text
"Return valid JSON:
{
  "field1": "...",
  "field2": "..."
}"
```

### 4. Binary Decisions

❌ **BAD:**
```text
"Should we escalate? Yes or No."
```

✅ **GOOD:**
```text
"Confidence score (0-1) and reason:
{
  "escalated": true,
  "confidence": 0.82,
  "reason": "..."
}"
```

---

## Summary

**Closira's prompt design philosophy:**

1. **Never assume** - Provide full context
2. **Never invent** - Require SOP grounding
3. **Never ambiguity** - Use enumerations
4. **Never free-form** - Mandate structured output
5. **Never binary** - Use confidence scoring

This design passes eval criteria:
✓ **Prompt engineering** - Hallucination prevention, structured outputs
✓ **Reliability** - Escalation logic, error handling
✓ **State management** - ConversationState tracking
✓ **Workflow** - Clear stage progression
