# Superpowers × Antigravity 2.0 — Gap Analysis

## 1. Currently Leveraged (✅ Good Coverage)

| Antigravity Feature | How Superpowers Uses It |
|---------------------|------------------------|
| `view_file` | Skill loading, code review, debugging |
| `run_command` | TDD test execution, builds, git operations |
| `write_to_file` / `replace_file_content` | Code implementation, task.md artifacts |
| `grep_search` | Codebase exploration in debugging/planning |
| `invoke_subagent` | SDD task dispatch, parallel agents |
| `define_subagent` | SDD implementer/reviewer type definitions |
| `ask_question` | Finishing-a-development-branch options |
| `search_web` | Research during brainstorming/debugging |
| `task.md` artifacts | Checklist tracking across all skills |
| Planning Mode | writing-plans, implementation_plan.md |
| Plugin system | plugin.json, GEMINI.md, skills/ directory |

## 2. Partially Leveraged (⚠️ Room to Improve)

| Antigravity Feature | Current State | Improvement Opportunity |
|---------------------|---------------|------------------------|
| **Artifacts system** | Only `task.md` used. Skills don't create `walkthrough.md`, `implementation_plan.md`, or rich artifacts with Mermaid/carousels. | Skills should generate proper typed artifacts (implementation_plan, walkthrough, task) with Mermaid diagrams, diff blocks, file links. |
| **`send_message`** | Used implicitly via subagent dispatch. No skill teaches peer-to-peer agent communication patterns. | SDD could leverage direct inter-agent messaging for coordination instead of just dispatch-and-wait. |
| **Workspace isolation** | `using-git-worktrees` mentions `Workspace: "branch"` but is very brief (~55 lines). | Could document `Workspace: "share"` pattern and when to use branch vs share. |

## 3. Completely Unleveraged (❌ Not Used At All)

| Antigravity Feature | What It Does | Potential Skill/Enhancement |
|---------------------|-------------|----------------------------|
| **`generate_image`** | Creates/edits images via Nano Banana Pro. Text rendering, UI mockups, infographics. | Replace the deleted brainstorm visual companion with native `generate_image`. No server needed — just generate mockups inline during brainstorming. |
| **`schedule` (cron)** | One-shot timers and recurring cron jobs | **New skill: scheduled-operations** — teach agents to set up recurring health checks, deployment monitors, periodic test runs, scheduled reminders. |
| **`manage_task`** | Background task lifecycle (list, kill, status, send_input) | Integrate with SDD — long-running builds/tests as background tasks instead of blocking the main agent. |
| **Browser automation** | Navigate pages, inspect DOM, take screenshots, record interactions | **New skill: browser-testing** — automated UI verification after frontend implementation. Screenshot comparison, DOM assertions. |
| **`read_url_content`** | Fetch web content as markdown | Skills could reference external docs, fetch API specs, pull in design references during brainstorming. |
| **`generate_image` for diagrams** | Architecture diagrams, flow charts, system overviews | writing-plans and brainstorming could generate visual architecture diagrams alongside text specs. |
| **MCP (Model Context Protocol)** | Connect to databases, Google Workspace, external tools | **New skill: mcp-integration** — guide agents through connecting to external data sources, using MCP tools in workflows. |
| **`/memory show` / `/memory reload`** | Inspect and refresh agent knowledge | **Enhance using-superpowers** — teach agents to check memory state, reload when instruction files change. |
| **Inline artifact comments** | Google Doc-style feedback on artifacts | Skills could instruct agents to use artifact comments for code review feedback instead of text dumps. |
| **`list_dir`** | Directory listing with metadata | Useful for project context exploration — brainstorming and debugging could use this more explicitly. |
| **Slash commands** | `/goal`, `/schedule`, `/browser`, `/grill-me` | Skills should recommend relevant slash commands (e.g., brainstorming could suggest `/grill-me` for interactive interviews). |
| **`list_permissions` / `ask_permission`** | Security-aware operations | Skills could teach agents to check permissions before operations and request minimal scope. |

## 4. Legacy Cleanup Still Needed

The **installed** copy of `using-superpowers/SKILL.md` (at `~/.gemini/config/plugins/`) still contains:
- Multi-platform "How to Access Skills" section (Claude Code, Copilot CLI, Gemini CLI references)
- "Platform Adaptation" section pointing to deleted reference files (codex-tools.md, copilot-tools.md, antigravity-tools.md)
- References to `Skill` tool, `TodoWrite`, `Invoke Skill tool` in the flow graph

> **Note:** The **workspace** copy is clean. This will resolve when the user upgrades the installed plugin.

## 5. Proposed New Skills / Enhancements

### New Skills

| Skill Name | Purpose | Key Antigravity Features Used |
|------------|---------|------------------------------|
| **visual-brainstorming** | Generate UI mockups, architecture diagrams, and design comparisons during brainstorming | `generate_image`, artifacts with embedded images |
| **browser-testing** | Automated UI verification — navigate pages, take screenshots, compare against expectations | Browser automation, screenshots, artifacts |
| **scheduled-operations** | Teach agents to set up cron jobs, health checks, deployment monitors | `schedule` (cron), `manage_task` |
| **mcp-integration** | Guide agents through connecting to external data sources | MCP tools, `mcp_config.json` |

### Enhancements to Existing Skills

| Skill | Enhancement |
|-------|-------------|
| **brainstorming** | Integrate `generate_image` for inline mockups (replaces deleted brainstorm server). Recommend `/grill-me` slash command for interactive design interviews. |
| **writing-plans** | Generate Mermaid architecture diagrams in plan artifacts. Use `implementation_plan.md` artifact type. |
| **subagent-driven-development** | Use `manage_task` for long-running build/test operations. Use `send_message` for inter-agent coordination. |
| **using-superpowers** | Document `/memory show` and `/memory reload`. Add `list_dir` to project context exploration. Recommend relevant slash commands. |

## 6. Priority Recommendation

### Phase 1: Quick Wins (enhance existing skills)
1. Brainstorming — add `generate_image` for mockups (replaces brainstorm server)
2. writing-plans — Mermaid diagrams in artifacts
3. using-superpowers — document memory commands and slash commands

### Phase 2: New Core Skills
4. visual-brainstorming or enhance brainstorming with visual companion
5. browser-testing skill
6. scheduled-operations skill

### Phase 3: Advanced Integration
7. mcp-integration skill
8. SDD enhancements (background tasks, inter-agent messaging)

> **Important:** This is a multi-project scope. Each phase should be its own spec → plan → implementation cycle per the brainstorming skill's decomposition guidance.
