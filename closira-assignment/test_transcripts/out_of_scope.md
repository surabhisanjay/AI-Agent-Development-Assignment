# Test Transcript 2: Out-of-Scope Question

## Scenario
Customer asks about information not available in SOP (side effects, recovery time).
FAQ returns LOW confidence, triggering escalation.

## Expected Flow
1. FAQ Agent answers with LOW confidence
2. Escalation Agent detects out_of_scope trigger
3. Customer routed to human specialist
4. Summary prepared for handoff

---

## Transcript

**Customer**: What are the side effects of Botox? How long does the treatment last?

**Assistant**: I don't have detailed information about side effects or treatment duration in my knowledge base. For medical and clinical questions, I'm connecting you with a specialist who can provide accurate information.

*[FAQ Agent: confidence=LOW, sop_match=false, needs_escalation=true]*
*[Escalation Agent: escalated=true, reason=out_of_scope, confidence=0.75]*

---

## Summary for Human Agent

- **Customer Intent**: Medical/clinical inquiry about Botox
- **Key Details**: Asked about side effects and duration
- **SOP Gaps**:
  - Botox side effects information not available
  - Botox duration/recovery information not available
- **Sentiment**: NEUTRAL
- **Recommended Action**: Route to clinical specialist for medical guidance
- **Assign To**: Clinical Specialists

---

## Notes
- Medical questions are high-priority for escalation
- Clinical specialist should provide evidence-based information
- Consider adding side effect information to SOP
