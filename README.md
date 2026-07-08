# SkillWeave SAD — Superpowers Skill Library

> Implementing the **Decompose → Retrieve → Compose** pipeline from [*SkillWeaver: Compositional Skill Routing for LLM Agents*](https://arxiv.org/pdf/2606.18051) — without MCP, without vector databases, for any IDE or CLI, configured via `.env`.

---

## What is SkillWeave SAD?

The paper identifies that naively loading all agent skills at once causes:
- **Context bloat** (99%+ of context wasted on irrelevant skills)
- **Attention loss** (agent ignores relevant skills buried in context)
- **Poor decomposition** (agent decomposes tasks without knowing which skills exist)

The fix is the **SAD (Skill-Aware Decomposition) pipeline**:

```
User Request (EVERY message goes through SAD first)
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ DECOMPOSE (Iterative SAD)                            │
│ Break request into atomic sub-tasks.                 │
│ Check skill-index.json for each sub-task.            │
│ Re-decompose if unmatched (DA feedback loop).        │
│ Target: DA = 1.0 (all sub-tasks → known skill)       │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ RETRIEVE                                             │
│ Load ONLY the matched SKILL.md files (1-4 max)       │
│ from the hidden library/ folder.                     │
│ 90-99% context window savings vs. loading all.       │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ COMPOSE (DAG)                                        │
│ Read skill-dag.json → topological sort.              │
│ Execute skills in dependency order.                  │
│ Each skill's output feeds the next.                  │
└──────────────────────────────────────────────────────┘
```

---

## Restructuring & Hiding Skills

To prevent the LLM from automatically loading all skills at once (which defeats the entire SAD architecture), **14 individual skills have been hidden in a separate `library/` directory**.

Only two visible entrypoints remain in `skills/`:
- **`skills/skillweave-orchestrator/`** — the SAD pipeline engine
- **`skills/using-superpowers/`** — the entrypoint trigger

All other 14 skills are hidden inside `library/` and retrieved dynamically on demand during execution.

---

## Configuration via `.env`

You can configure the API endpoint and provider for the SAD routing pipeline via a `.env` file at the root of the workspace.

See [.env.example](.env.example) for setup:
```env
SKILLWEAVE_PROVIDER=lmstudio
SKILLWEAVE_MODEL=
SKILLWEAVE_API_KEY=
SKILLWEAVE_BASE_URL=http://localhost:1234/v1
```

### Supported Providers
- **LM Studio**: (Default) Set `SKILLWEAVE_PROVIDER=lmstudio` and `SKILLWEAVE_BASE_URL=http://localhost:1234/v1`
- **Ollama**: Set `SKILLWEAVE_PROVIDER=ollama` and `SKILLWEAVE_BASE_URL=http://localhost:11434/v1`
- **Gemini**: `gemini-2.5-pro | gemini-2.0-flash | gemini-1.5-pro`
- **Anthropic**: `claude-3-5-sonnet-20241022 | claude-3-haiku-20240307`
- **OpenAI**: `gpt-4o | gpt-4o-mini | o1`

---

## Standalone Python Runner

A zero-dependency Python script [skillweave.py](skillweave.py) runs the SAD pipeline on any machine:
```bash
python skillweave.py "I want to add a dark mode toggle to my React app"
```
It reads the `.env` settings, executes SAD decomposition via the selected LLM, semantically matches tasks against the `skill-index.json` triggers, retrieves the required skills from `library/`, and outputs a topologically sorted DAG execution plan.

---

## Setup by IDE / CLI (Mandatory First-Use)

To ensure that the agent runs the SAD orchestrator on the very first request, the configuration files for all platforms are configured as **strict first-use mandates**.

- **Claude Code**: reads [`CLAUDE.md`](./CLAUDE.md)
- **Cursor**: reads [`.cursor/rules/skillweave-sad.mdc`](./.cursor/rules/skillweave-sad.mdc)
- **Cline**: reads [`.clinerules`](./.clinerules)
- **Aider**: reads [`CONVENTIONS.md`](./CONVENTIONS.md)
- **Generic CLI**: reads [`AGENTS.md`](./AGENTS.md)

Each file mandates that the agent read `.agents/plugins/superpowers/skills/skillweave-orchestrator/SKILL.md` before responding or performing any action.

---

## Key Files

```
SkillWeave SAD/
├── AGENTS.md                           Universal entry point (all IDEs/CLIs)
├── CLAUDE.md                           Claude Code adapter
├── CONVENTIONS.md                      Aider adapter
├── .clinerules                         Cline adapter
├── .cursor/rules/skillweave-sad.mdc    Cursor adapter
├── .env.example                        Configuration template
├── .gitignore                          Ignores local .env
├── skillweave.py                       Zero-dependency Python SAD CLI
└── .agents/plugins/superpowers/
    ├── skills/
    │   ├── skill-index.json            ← LOAD THIS FIRST (retrieval index)
    │   ├── skill-dag.json              ← Dependency graph (DAG)
    │   └── skillweave-orchestrator/    ← Full SAD pipeline
    └── library/                        ← Isolated, hidden skills
        ├── brainstorming/SKILL.md
        ├── writing-plans/SKILL.md
        ├── ... (all other 12 skills)
```

---

## Adding New Skills

When adding new skills:
1. Create a directory in `library/<new-skill>/` and place your `SKILL.md` inside it.
2. Add the skill to `skills/skill-index.json` with the path pointing to `library/<new-skill>/SKILL.md`.
3. Add dependency edges to `skills/skill-dag.json`.
