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

## The SAD Execution Pipeline

To maintain maximum token efficiency and execute the precise routing algorithm, you MUST run the Python router script rather than attempting to manually parse the skill index in your context.

### Step 1 — Run the Router Script

Run the `skillweave.py` script on the user's request:

```bash
python .agents/skillweave.py "<raw user request>"
```

### Step 2 — Parse the Output

The script executes the full SAD pipeline:
1. **Decomposes** the query into atomic sub-tasks (calling the local/configured LLM).
2. **Retrieves** matching candidate skills per sub-task (using embeddings via `sentence-transformers` if available, or falling back to a pure-Python TF-IDF semantic retriever).
3. Enforces the **SAD Feedback Loop** with Jaccard convergence to refine sub-tasks.
4. Performs **Compatibility-Weighted Selection (Eq. 4)** to select the best skills.
5. Generates the final **topologically-sorted DAG plan**.

### Step 3 — Load ONLY the Matched Skills

From the script's output, identify the list of unique skills in the execution plan. For each matched skill, load its instructions:

```
view_file: .agents/plugins/superpowers/library/<skill-name>/SKILL.md
```

> [!IMPORTANT]
> **Context Efficiency Rule**:
> Load ONLY the skills you will execute in this plan. Do NOT pre-load other skills "just in case". This achieves a **99% token savings** by keeping irrelevant skills hidden from your active context.

### Step 4 — Announce the Plan & Execute

Before performing any tasks, present the execution plan to the user:

```
I'm using the SkillWeave SAD orchestrator. Here's my execution plan:

1. <skill-1> — <description of step 1>
2. <skill-2> — <description of step 2>
...
```

Then proceed to execute each skill sequentially in the DAG-sorted order, carrying output artifacts forward.

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
