# MANDATORY FIRST ACTION — NO EXCEPTIONS

Before you answer any user query, ask any clarifying questions, browse the codebase, or execute any commands, you MUST read and execute the SkillWeave SAD Orchestrator:

File path:
`.agents/plugins/superpowers/skills/skillweave-orchestrator/SKILL.md`

## The SAD Routing Rule
1. **EVERY message** the user sends must go through the SAD (Skill-Aware Decomposition) pipeline first, before hitting the main LLM.
2. Read the orchestrator skill first to decompose the request, check the `skills/skill-index.json` catalog, and compose a DAG-ordered execution plan.
3. Load only the specific skills retrieved by the orchestrator from the hidden `library/` directory.
4. Default API provider is **LMStudio** (`http://localhost:1234/v1`). Check `.env` at the root for provider configuration.

No excuses, no deviations. Route every request through the orchestrator first.
