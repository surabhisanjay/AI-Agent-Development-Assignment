# Test Transcript 3: Complaint Escalation

## Scenario
Customer expresses dissatisfaction with service quality.
Sentiment analysis detects complaint, triggering immediate escalation.

## Expected Flow
1. FAQ Agent processes initial question
2. Escalation Agent detects negative sentiment/complaint
3. Escalation triggered immediately
4. Routed to Support Escalation Queue

---

## Transcript

**Customer**: I'm absolutely unhappy with the service you provided. Your staff was rude and unprofessional!

**Assistant**: I'm sorry to hear you're experiencing issues. Let me get a specialist to help you right away.

*[Escalation Agent: complaint_detected=true, confidence=0.95]*
*[Escalation Agent: escalated=true, reason=complaint]*

---

## Summary for Human Agent

- **Customer Intent**: Service complaint
- **Key Details**: 
  - Reported rude/unprofessional staff behavior
  - High dissatisfaction
- **Sentiment**: NEGATIVE
- **Recommended Action**: Escalate to senior support specialist with emphasis on resolution
- **Assign To**: Support Escalation Queue
- **Priority**: HIGH - Negative sentiment detected

---

## Notes
- Immediate human response required
- Apology and resolution focus needed
- Possible compensation consideration
- Follow-up quality check recommended
