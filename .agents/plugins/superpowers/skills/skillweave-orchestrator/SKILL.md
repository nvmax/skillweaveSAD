---
name: skillweave-orchestrator
description: "Implements the SkillWeave SAD pipeline on EVERY user message: Decompose the request into atomic sub-tasks, Retrieve matching skills from skill-index.json, and Compose a dependency-ordered execution plan. This is the master orchestrator — the engine that invokes all other skills in the correct order."
triggers:
  - "*"
outputs:
  - executed-plan
depends_on: []
next_skills: []
atomic: false
---

# SkillWeave SAD Orchestrator

Implements the **Decompose → Retrieve → Compose** pipeline from *SkillWeaver: Compositional Skill Routing for LLM Agents* (arXiv 2606.18051), adapted for in-context skill routing without MCP or vector databases.

**Core innovation:** Iterative Skill-Aware Decomposition (SAD) — decompose iteratively until every sub-task maps to a known skill, reducing context overhead by 99%+ versus loading all skills at once.

---

## When to Use This Skill

This skill is executed on **EVERY** user request. Every single message from the user must go through the SAD pipeline first, to determine what skills should be used before calling the main API LLM.

Only subagents executing a specific parallel task skip this orchestration step.

---

## Phase 1: DECOMPOSE — Iterative Skill-Aware Decomposition (SAD)

### Step 1.1 — Read the Skill Index

```
view_file: .agents/plugins/superpowers/skills/skill-index.json
```

This is the only file you load at the start. It contains all skill names, descriptions, triggers, and dependencies in ~3KB — instead of loading all 15 SKILL.md files (~50KB total).

### Step 1.2 — Initial Decomposition

Break the user's request into atomic candidate sub-tasks. Each sub-task should be:
- **Atomic**: a single, clear action
- **Bounded**: has a defined start and end
- **Independent or explicitly dependent**: knows what it needs as input

**Example:**
> User: "I want to add a dark mode toggle to my React app"

Initial decomposition:
1. Design the dark mode feature
2. Plan the implementation
3. Implement the toggle component
4. Write tests
5. Verify it works

### Step 1.3 — SAD Alignment Check (THE CRITICAL LOOP)

For each candidate sub-task, check `skill-index.json`:

```
FOR each sub-task:
  SEARCH skill-index.json — do any skill's triggers, name, or description
  semantically match this sub-task?

  IF match found:
    Record: (sub-task, matched_skill)
    CONTINUE to next sub-task

  IF no match found:
    → This sub-task is at wrong granularity
    → RE-DECOMPOSE: split it into smaller sub-tasks OR merge it with adjacent sub-task
    → REPEAT alignment check on the new sub-tasks
    → ITERATE until match found (maximum 3 iterations)

  IF still no match after 3 iterations:
    → Flag as "no skill available"
    → Handle with general agent capability (not skill-driven)
```

**SAD Alignment Example:**

| Sub-task | First check | Action | Aligned skill |
|----------|-------------|--------|---------------|
| "Design dark mode feature" | triggers: "design", "create", "new feature" → `brainstorming` ✓ | Match | `brainstorming` |
| "Plan implementation" | triggers: "implementation plan", "plan" → `writing-plans` ✓ | Match | `writing-plans` |
| "Implement toggle" | triggers: "implement", "code", "TDD" → `test-driven-development` ✓ | Match | `test-driven-development` |
| "Write tests" | triggers: "write tests", "TDD" → `test-driven-development` ✓ | Merge with above | `test-driven-development` |
| "Verify it works" | triggers: "verify", "validate" → `verification-before-completion` ✓ | Match | `verification-before-completion` |

Decomposition Alignment (DA) = 4/4 = 1.0 ✓ (target: all sub-tasks mapped)

**Re-decomposition Example (SAD feedback):**

Sub-task: "Set up the dark mode system" — no direct match in skill-index.json

SAD re-decomposes:
- "Design the dark mode system" → `brainstorming` ✓
- "Plan how to implement it" → `writing-plans` ✓

Both now align. DA achieved. ✓

### Step 1.4 — Confirm the Sub-Task Map

After SAD alignment, you have:
```
[(sub-task-1, skill-A), (sub-task-2, skill-B), (sub-task-3, skill-C), ...]
```

Each sub-task is now grounded to a specific skill in the library.

---

## Phase 2: RETRIEVE — Load Only Matched Skills

### Step 2.1 — Identify Unique Skills Needed

From the sub-task map, extract the **unique set** of skills required:
```
required_skills = unique([skill for (sub-task, skill) in sub-task-map])
```

### Step 2.2 — Load ONLY Those Skills

For each required skill, load its SKILL.md using the path from `skill-index.json`:

```
view_file: .agents/plugins/superpowers/library/<skill-name>/SKILL.md
```

**Context efficiency rule:**
- Load ONLY the skills you will execute in this plan
- Do NOT pre-load skills "just in case"
- If a new skill becomes needed mid-execution, load it then

**Why this matters (from the paper):**
Loading all 15 SKILL.md files = ~50,000 tokens in context.
Loading only 2-4 needed skills = ~2,000-5,000 tokens.
That's a **90-99% reduction** in context window consumption.

---

## Phase 3: COMPOSE — Build the Execution Plan

### Step 3.1 — Load the DAG

```
view_file: .agents/plugins/superpowers/skills/skill-dag.json
```

### Step 3.2 — Topological Sort

Using the DAG edges, determine the correct execution order:

1. Find all skills with no `depends_on` prerequisites that are in your required_skills → these run first
2. After each skill completes, unlock skills whose `depends_on` are now satisfied
3. Handle alternatives (either `executing-plans` OR `subagent-driven-development`, not both)
4. Handle concurrent skills (run them in parallel if possible)

**Example DAG execution order for "Add dark mode":**
```
brainstorming
    ↓ (output: design-spec)
writing-plans
    ↓ (output: implementation-plan)
test-driven-development
    ↓ (output: passing-tests)
verification-before-completion
    ↓ (output: verified-deliverable)
finishing-a-development-branch
```

### Step 3.3 — Announce the Plan

Before executing, present the composed plan to the user:

```
I'm using the SkillWeave SAD orchestrator. Here's my execution plan:

1. brainstorming — Design the dark mode feature with you
2. writing-plans — Create the implementation plan
3. test-driven-development — Implement with TDD
4. verification-before-completion — Verify everything works
5. finishing-a-development-branch — Create PR and merge

Proceeding now. You can stop me at any step.
```

---

## API / LLM Configuration via `.env`

The orchestrator uses `.env` at the workspace root to determine which LLM API provider to use for any automated planning or routing logic.

### Supported Providers
- **LM Studio**: (Default) Set `SKILLWEAVE_PROVIDER=lmstudio`, `SKILLWEAVE_BASE_URL=http://localhost:1234/v1`, `SKILLWEAVE_MODEL=your-local-model`
- **Ollama**: Set `SKILLWEAVE_PROVIDER=ollama`, `SKILLWEAVE_BASE_URL=http://localhost:11434/v1`, `SKILLWEAVE_MODEL=your-ollama-model`
- **Gemini**: Set `SKILLWEAVE_PROVIDER=gemini`, `SKILLWEAVE_API_KEY=xxx`, `SKILLWEAVE_MODEL=gemini-2.0-flash`
- **Anthropic**: Set `SKILLWEAVE_PROVIDER=anthropic`, `SKILLWEAVE_API_KEY=xxx`, `SKILLWEAVE_MODEL=claude-3-5-sonnet-20241022`
- **OpenAI**: Set `SKILLWEAVE_PROVIDER=openai`, `SKILLWEAVE_API_KEY=xxx`, `SKILLWEAVE_MODEL=gpt-4o`

The orchestrator reads this `.env` configuration file to instantiate the appropriate API client.

---

## Phase 4: EXECUTE — Run Skills in DAG Order

For each step in the composed plan:

1. **Load the skill** (if not already loaded from Phase 2): `view_file: .agents/plugins/superpowers/library/<name>/SKILL.md`
2. **Announce**: "Using `<skill-name>` to [purpose]"
3. **Execute the skill** exactly as its SKILL.md instructs
4. **Pass outputs** to the next dependent skill (e.g., design-spec → writing-plans)
5. **Update task tracking** as each skill completes

### Execution Rules

**Do not skip skills.** If brainstorming is in the plan, do brainstorming. If the user says "skip design, just implement," note this and collapse the plan accordingly — but don't silently skip.

**Carry outputs forward.** Each skill produces artifacts (design-spec, implementation-plan, etc.) that the next skill needs. Reference them explicitly when invoking the next skill.

**Handle blocked skills.** If a skill cannot complete (user cancels, blocker hit), stop and report. Do not proceed to dependent skills without their prerequisites.

---

## SAD Quality Metrics

After decomposition, verify alignment quality:

```
DA (Decomposition Alignment) = (# sub-tasks mapped to skills) / (# total sub-tasks)

Target: DA = 1.0 (all sub-tasks mapped)
Acceptable: DA ≥ 0.8 (≤1 sub-task unmatched)
Needs re-decomposition: DA < 0.8
```

**CatR@1 (Category Recall at 1):** For each sub-task, is the top-matched skill in the correct category?
- planning sub-tasks → planning skills ✓
- implementation sub-tasks → implementation skills ✓
- debugging sub-tasks → debugging skills ✓

---

## Subagent Guard

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill. You have a specific task; the SAD pipeline is for top-level complex requests, not subagent execution.
</SUBAGENT-STOP>

---

## Examples

See `skills/skillweave-orchestrator/examples/sad-alignments.md` for 5 detailed worked examples of the SAD pipeline on real user requests.
