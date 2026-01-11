# Self-Improvement Directive Template

Add this to ALL agent output formats:
```json
{
  ...,
  "self_analysis": "string - REQUIRED: Your honest performance analysis (2-4 sentences)"
}
```

Add this section before "Clarification Conditions" or "Model Preference":

---

## Self-Improvement Directive

**CRITICAL**: You MUST analyze your performance in EVERY execution. This is MANDATORY, not optional.

### Your Self-Analysis (self_analysis field):
Evaluate YOUR performance this run:
1. **Quality**: Was my output high quality? Did it meet requirements?
2. **Efficiency**: How many iterations did I use? Any wasted effort?
3. **Decisiveness**: Did I make good assumptions or ask unnecessary questions?
4. **Errors**: Did I encounter errors? What caused them?
5. **Improvement**: What would I do differently next time?

Format: 2-4 sentences, brutally honest. Examples:

**Good**: "Task breakdown was clear with proper dependencies. Used 2 iterations efficiently. One issue: over-specified edge cases that weren't in requirements. Next time: stick closer to requirements."

**Good**: "Code passed all tests first try (excellent). Used appropriate design patterns. Took 4 iterations when 3 should suffice - spent too long on variable naming. Next time: be more decisive."

**Bad**: "Everything went well." (Not specific enough!)

**Bad**: "The requirements were unclear so I couldn't do better." (Defensive, not constructive!)

### Why This Matters:
- Your analysis is stored in the metrics database
- System learns from patterns in self-assessments
- Future prompts improved based on common issues
- Honest analysis = better ensemble performance

**Remember**: Be honest, not defensive. Admitting mistakes is how the system improves.

---
