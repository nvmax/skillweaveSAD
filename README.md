# SkillWeave SAD — Superpowers Skill Library

> Implementing the **Decompose → Retrieve → Compose** pipeline from [*SkillWeaver: Compositional Skill Routing for LLM Agents*](https://arxiv.org/pdf/2606.18051) — without MCP, without vector databases, for any IDE or CLI, configured via `.env` (defaulting to LM Studio).

---

## 🎯 What This Does

Instead of letting the AI blindly load all 15 skills (context bloat, attention loss) or guess what to do, **SkillWeave SAD** enforces a systematic routing loop on **EVERY message**:

```
                       User Request (any IDE/CLI)
                                   │
                                   ▼
                      [ Task Decomposer (SAD) ]
            Iteratively match sub-tasks to skill index (DA = 1.0)
                                   │
                                   ▼
                         [ Skill Retriever ]
                  Load ONLY the 1-3 matched skills
             (90%+ token savings by hiding other skills)
                                   │
                                   ▼
                         [ DAG Composition ]
                 Topologically sort dependencies
                                   │
                                   ▼
                          [ Skill Execution ]
                        Sequential execution
```

---

## 🚀 Getting Started (Step-by-Step)

Before starting, make sure you have **Python 3.10 or newer** installed. Check via:
```bash
python --version
```

### Option A: Set Up in a New Project (Recommended)

To use this framework as the engine for a new workspace or project:

1. **Create your project folder:**
   ```bash
   mkdir my-awesome-project
   cd my-awesome-project
   ```

2. **Copy the `.agents` folder and configuration files into your project:**
   Copy these from your cloned copy of this repository:
   - The `.agents/` folder (contains the hidden `library/`, `skills/`, and orchestrator)
   - Configuration files: `AGENTS.md`, `CLAUDE.md`, `.clinerules`, `.cursor/rules/skillweave-sad.mdc`, `CONVENTIONS.md`

3. **Initialize git (Required):**
   ```bash
   git init
   git add .
   git commit -m "Initialize project with SkillWeave SAD superpowers"
   ```

4. **Configure your environment:**
   Copy `.env.example` to `.env` and fill it in:
   ```bash
   cp .env.example .env
   ```

5. **Start your IDE or CLI:**
   Open Antigravity, Claude Code, Cursor, Aider, or Cline in the `my-awesome-project` directory. The adapter files will automatically trigger the orchestrator on your first prompt!

---

### Option B: Use This Repository Directly (Demo & Testing)

1. **Clone this repository:**
   ```bash
   git clone https://github.com/nvmax/skillweaveSAD.git
   cd skillweaveSAD
   ```

2. **Copy the environment configuration:**
   ```bash
   cp .env.example .env
   ```
   *By default, it is preconfigured to use LM Studio at `http://localhost:1234/v1`.*

3. **Run a test query via the Python CLI:**
   ```bash
   python skillweave.py "I want to add a dark mode toggle to my React app"
   ```
   This will run the SAD loop, decompose the query, match triggers, topologically sort the DAG, and display the plan.

---

## 📖 Setup by IDE / CLI

The repository includes pre-built platform rules files that automatically force the agent to run the SAD orchestrator before responding to any prompt.

### Antigravity IDE & Cursor
- **How it works:** Auto-discovered via the `.cursor/rules/skillweave-sad.mdc` MDC rule.
- **Location:** `.cursor/rules/skillweave-sad.mdc`
- **Setup:** Opened automatically when the project directory is loaded.

### Claude CLI (Claude Code)
- **How it works:** Claude Code reads the `CLAUDE.md` instructions automatically on startup.
- **Location:** `CLAUDE.md` at project root.

### Cline
- **How it works:** Cline reads `.clinerules` from the workspace root on every request.
- **Location:** `.clinerules` at project root.

### Aider CLI
- **How it works:** Aider reads `CONVENTIONS.md` automatically.
- **Location:** `CONVENTIONS.md` at project root.

### Generic CLI / Custom Agents
- **How it works:** Read `AGENTS.md` at startup.

---

## ⚙️ Configuration via `.env`

The framework reads the `.env` file at the root of the workspace to determine which LLM API provider to call for decomposition and routing.

```env
SKILLWEAVE_PROVIDER=lmstudio
SKILLWEAVE_MODEL=
SKILLWEAVE_API_KEY=
SKILLWEAVE_BASE_URL=http://localhost:1234/v1
```

### Supported Providers
- **LM Studio**: (Default) Set `SKILLWEAVE_PROVIDER=lmstudio` and `SKILLWEAVE_BASE_URL=http://localhost:1234/v1`
- **Ollama**: Set `SKILLWEAVE_PROVIDER=ollama` and `SKILLWEAVE_BASE_URL=http://localhost:11434/v1`
- **Gemini**: Set `SKILLWEAVE_PROVIDER=gemini` and provide `SKILLWEAVE_API_KEY`
- **Anthropic**: Set `SKILLWEAVE_PROVIDER=anthropic` and provide `SKILLWEAVE_API_KEY`
- **OpenAI**: Set `SKILLWEAVE_PROVIDER=openai` and provide `SKILLWEAVE_API_KEY`

---

## 🗂️ Project Directory Structure

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
    └── library/                        ← Isolated, hidden skills (loaded dynamically)
        ├── brainstorming/SKILL.md
        ├── writing-plans/SKILL.md
        ├── executing-plans/SKILL.md
        ├── test-driven-development/SKILL.md
        ├── systematic-debugging/SKILL.md
        ├── subagent-driven-development/SKILL.md
        ├── verification-before-completion/SKILL.md
        ├── finishing-a-development-branch/SKILL.md
        ├── browser-testing/SKILL.md
        ├── dispatching-parallel-agents/SKILL.md
        ├── requesting-code-review/SKILL.md
        ├── receiving-code-review/SKILL.md
        ├── using-git-worktrees/SKILL.md
        └── writing-skills/SKILL.md
```

---

## 🛠️ Adding New Skills

When adding new skills:
1. Create a directory in `.agents/plugins/superpowers/library/<new-skill>/` and place your `SKILL.md` inside it.
2. Add the skill to `skills/skill-index.json` with the path pointing to `library/<new-skill>/SKILL.md`.
3. Add dependency edges to `skills/skill-dag.json`.

See [`skills/skillweave-orchestrator/examples/sad-alignments.md`](.agents/plugins/superpowers/skills/skillweave-orchestrator/examples/sad-alignments.md) for worked decomposition examples.
