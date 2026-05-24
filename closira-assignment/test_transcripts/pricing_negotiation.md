# Test Transcript 5: Pricing Negotiation

## Scenario
Customer inquires about custom pricing or bulk discounts.
Pricing negotiation triggers escalation to Sales Team.

## Expected Flow
1. FAQ Agent provides standard pricing
2. Customer asks for discount/custom quote
3. Escalation Agent detects pricing_negotiation
4. Routed to Sales Team

---

## Transcript

**Customer**: What are your prices for Botox?

**Assistant**: Botox treatments start from £200. We offer various packages depending on your needs.

*[FAQ Agent: confidence=HIGH, sop_match=true]*

**Customer**: That's quite expensive. Do you offer any bulk discounts for my clinic?

*[Escalation Agent: pricing_negotiation=true, confidence=0.80]*
*[Escalation Agent: escalated=true, reason=pricing_negotiation]*

**Assistant**: For custom pricing and special arrangements, I'll connect you with our sales team.

---

## Summary for Human Agent

- **Customer Intent**: Bulk purchase inquiry with price negotiation
- **Key Details**:
  - Interested in Botox services
  - Looking for bulk/clinic pricing
  - Price-sensitive
- **SOP Gaps**: None
- **Sentiment**: NEUTRAL
- **Recommended Action**: Assign to sales representative for custom quote
- **Assign To**: Sales Team

---

## Notes
- High conversion potential if handled by sales
- Prepare custom pricing proposal for clinic-scale usage
- Consider relationship development opportunity
