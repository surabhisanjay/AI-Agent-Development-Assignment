# Test Transcript 6: Multiple Unanswered Questions

## Scenario
Customer asks 3+ questions where SOP lacks information.
Escalation triggered after 2 unanswered questions.

## Expected Flow
1. FAQ Agent returns LOW confidence for Q1
2. FAQ Agent returns LOW confidence for Q2
3. unanswered_count > 2, escalation triggered
4. Routed to Knowledge Specialist

---

## Transcript

**Customer**: Can Botox be combined with other treatments? What's the recovery time?

**Assistant**: I don't have specific information about combining treatments or recovery times. A specialist can help with these details.

*[FAQ Agent Q1: confidence=LOW]*
*[FAQ Agent Q2: confidence=LOW]*
*[unanswered_count = 2]*

**Customer**: Will I see results immediately?

**Assistant**: I want to make sure you get the right answers. Let me transfer you to a specialist on our team.

*[Escalation Agent: unanswered_count > max (3 > 2)]*
*[Escalation Agent: escalated=true, reason=multiple_unanswered, confidence=0.85]*

---

## Summary for Human Agent

- **Customer Intent**: Comprehensive information about Botox treatment
- **Key Details**:
  - Multiple clinical questions
  - Interested in treatment details and timeline
- **SOP Gaps**:
  - Treatment combination guidelines not available
  - Recovery time information not available
  - Expected results timeline not available
- **Sentiment**: NEUTRAL
- **Recommended Action**: Assign to knowledge specialist
- **Assign To**: Knowledge Specialists

---

## Notes
- Pattern indicates knowledge base gaps
- Consider expanding SOP with clinical information
- Schedule consultation with customer to address all questions
- Recommend scheduling with clinical consultant
