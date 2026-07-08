---
name: using-superpowers
description: Use on EVERY user message - routes the request through the SkillWeave SAD pipeline (Decompose, Retrieve, Compose) before hitting the main LLM.
# SkillWeave SAD metadata — used by skillweave-orchestrator for decomposition alignment
triggers:
  - "*"
outputs:
  - skill-invocation-plan
depends_on: []
next_skills:
  - skillweave-orchestrator
atomic: false
category: meta
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
EVERY message the user sends MUST go through the SkillWeave SAD pipeline before hitting the main API LLM.
You have no choice. You cannot bypass this rule.
</EXTREMELY-IMPORTANT>

## The Rule

**For EVERY message the user sends, route it through the SkillWeave SAD orchestrator first**:

```
Read: .agents/plugins/superpowers/skills/skill-index.json
Then: invoke .agents/plugins/superpowers/skills/skillweave-orchestrator/SKILL.md
```

The SAD orchestrator will decompose the request, check the skill index, retrieve only the necessary SKILL.md files from the `.agents/plugins/superpowers/library/` folder, compose the DAG, and execute them.

This ensures you determine which skills are needed before responding. Only subagents bypass this step.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills carry it out. The SAD pipeline automatically enforces this via the dependency DAG.

- "Let's build X" → SAD pipeline → brainstorming first, then implementation skills.
- "Fix this bug" → `systematic-debugging` first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## User Instructions

User instructions (GEMINI.md, AGENTS.md, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.

