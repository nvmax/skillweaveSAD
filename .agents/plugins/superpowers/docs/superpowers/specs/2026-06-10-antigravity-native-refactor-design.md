# Antigravity-Native Superpowers Refactor

## Goal

Fork superpowers into an Antigravity 2.0-exclusive version that strips all multi-platform compatibility layers, rewrites skills to use native Antigravity tool names directly, and leverages platform-specific capabilities (`define_subagent`, `ask_question`, `generate_image`, `schedule`, `Workspace: "branch"`) for better UX, lower token consumption, and higher-quality workflows.

## Background

Superpowers v5.1.0 supports 9 platforms: Antigravity 2.0, Claude Code, Codex CLI, Codex App, Factory Droid, Gemini CLI, OpenCode, Cursor, and GitHub Copilot CLI. This cross-platform support adds significant overhead:

- **Tool name indirection:** Skills use Claude Code tool names (`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `TodoWrite`, `Task`, `Skill`). Non-CC platforms must consult a tool mapping reference file to translate.
- **Multi-platform routing:** `using-superpowers/SKILL.md` contains a 5-platform if/else block for how to access skills.
- **Legacy fallback skills:** `executing-plans` exists solely as a fallback for platforms without subagent support.
- **Heavyweight visual companion:** A Node.js server (`scripts/server.cjs`) is used for visual brainstorming because most platforms lack native image generation.
- **Polyglot hook scripts:** Cross-platform CMD/bash wrappers for session-start hooks.
- **9 manifest files:** `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.opencode/`, `gemini-extension.json`, `plugin.json`, each needing version sync.

By targeting Antigravity 2.0 exclusively, we eliminate all of this.

## User Review Required

> [!IMPORTANT]
> This refactor creates a hard fork. The resulting codebase will no longer work with Claude Code, Codex, Cursor, Gemini CLI, OpenCode, or Copilot CLI. This is intentional per user direction.

> [!WARNING]
> The `writing-skills` skill (656 lines) references Claude Code-specific testing methodology (`claude -p` headless mode), `~/.claude/skills` directories, and `@` syntax warnings. This rewrite is the largest single task.

## Proposed Changes

Changes are grouped by component and ordered dependencies-first.

---

### Component 1: Delete Legacy Platform Support

Remove all files that serve platforms other than Antigravity 2.0.

#### [DELETE] `.claude-plugin/` (directory)
Claude Code plugin manifest and marketplace registration.

#### [DELETE] `.codex-plugin/` (directory)
Codex plugin manifest with rich interface block.

#### [DELETE] `.cursor-plugin/` (directory)
Cursor plugin manifest.

#### [DELETE] `.opencode/` (directory)
OpenCode plugin runtime (ES module) and install docs.

#### [DELETE] `hooks/` (directory)
Polyglot CMD/bash hook wrappers and session-start scripts. Antigravity 2.0 boots via `contextFileName` in `gemini-extension.json` → `GEMINI.md` → auto-loads `using-superpowers/SKILL.md`. No hooks needed.

#### [DELETE] `scripts/sync-to-codex-plugin.sh`
Codex marketplace sync tool. No longer relevant.

#### [DELETE] `scripts/bump-version.sh` and `.version-bump.json`
Version sync across 9 manifests. With only `plugin.json` and `gemini-extension.json` remaining, manual version management is trivial.

#### [DELETE] `skills/using-superpowers/references/copilot-tools.md`
#### [DELETE] `skills/using-superpowers/references/codex-tools.md`
#### [DELETE] `skills/using-superpowers/references/gemini-tools.md`
#### [DELETE] `skills/using-superpowers/references/antigravity-tools.md`
All tool mapping references. No longer needed because skills will use native Antigravity tool names directly.

#### [DELETE] `skills/executing-plans/` (directory)
Fallback skill for platforms without subagent support. Antigravity 2.0 always has subagents; `subagent-driven-development` is the only execution path.

#### [DELETE] `tests/claude-code/` (directory)
Claude Code integration tests.

#### [DELETE] `tests/codex-plugin-sync/` (directory)
Codex sync tests.

#### [DELETE] `tests/opencode/` (directory)
OpenCode integration tests.

#### [DELETE] `docs/README.opencode.md`
OpenCode integration guide.

#### [DELETE] `docs/windows/polyglot-hooks.md`
Polyglot hook documentation (hooks are deleted).

---

### Component 2: Rewrite Skills to Use Native Tool Names

Replace all Claude Code tool name references with direct Antigravity 2.0 tool names. This eliminates the translation layer entirely.

#### Tool Name Substitutions (applied across all skills):

| Claude Code name | Antigravity 2.0 native | Notes |
|-----------------|----------------------|-------|
| `Read` | `view_file` | |
| `Write` | `write_to_file` | |
| `Edit` | `replace_file_content` / `multi_replace_file_content` | Single contiguous block vs multiple non-adjacent blocks |
| `Bash` | `run_command` | |
| `Grep` | `grep_search` | Replaces both `git grep` and `grep` shell commands |
| `Glob` | `find_by_name` | Replaces `find . -name` shell commands |
| `TodoWrite` | `write_to_file` creating `task.md` artifact | Use `IsArtifact: true`, `ArtifactType: "task"` |
| `Skill` tool | `view_file` on `SKILL.md` | Skills auto-load from plugins |
| `Task` tool | `invoke_subagent` | See Component 3 |
| `WebSearch` | `search_web` | |
| `WebFetch` | `read_url_content` | |
| `EnterWorktree` | `Workspace: "branch"` on `invoke_subagent` | See Component 5 |

#### Shell Command Substitutions (applied across all skills):

| Shell command pattern | Antigravity 2.0 native | Benefit |
|----------------------|----------------------|---------|
| `find . -name "*.js"` | `find_by_name` with Pattern/Extensions | Cross-platform (Windows safe) |
| `git grep`, `grep -r` | `grep_search` | No terminal approval needed |
| `git check-ignore` | `run_command` | Still needs shell for git-specific ops |

#### [MODIFY] `skills/using-superpowers/SKILL.md`

- Remove the 5-platform "How to Access Skills" block (lines 30-38).
- Replace with single Antigravity-native instruction: "Skills auto-load from plugins. Use `view_file` to read any `SKILL.md` on demand."
- Remove "Platform Adaptation" section (line 42) and all references to tool mapping files.
- Replace `TodoWrite` references in flowchart (lines 60, 74, 76) with `task.md artifact`.
- Replace `Skill tool` references with `view_file`.

#### [MODIFY] `skills/subagent-driven-development/SKILL.md`

- Replace all `TodoWrite` references (lines 60, 63, 68, 81, 82, 135) with `task.md artifact`.
- Replace `Task tool` dispatch syntax with `invoke_subagent` / `define_subagent` (see Component 3).
- Replace `./implementer-prompt.md` references with `define_subagent` type references.
- Remove "executing-plans" as alternative workflow (lines 278-279) since it's deleted.

#### [MODIFY] `skills/brainstorming/SKILL.md`

- Replace `TodoWrite` checklist tracking with `task.md artifact`.

#### [MODIFY] `skills/requesting-code-review/SKILL.md`

- Replace `Task tool (general-purpose)` reference (line 34) with `invoke_subagent` using the `code-reviewer` defined type.

#### [MODIFY] `skills/writing-plans/SKILL.md`

- Remove execution handoff choice between subagent-driven and inline (lines 136-152). Only subagent-driven-development remains.
- Replace `TodoWrite` reference patterns.

#### [MODIFY] `skills/writing-skills/SKILL.md`

- Replace `TodoWrite` reference (line 598) with `task.md artifact`.
- Remove `@` syntax warning (lines 286-288) — CC-specific.
- Replace `~/.claude/skills` directory references with `~/.gemini/config/plugins/`.
- Replace `claude -p` headless testing references with `agy --print` headless testing.
- Remove multi-platform personal skill directory listing (line 12).

#### [MODIFY] `skills/systematic-debugging/SKILL.md`

- Replace shell-based file searching instructions with `grep_search` and `find_by_name`.

#### [MODIFY] `skills/test-driven-development/SKILL.md`

- Replace `@testing-anti-patterns.md` reference (line 359) — `@` is CC-specific syntax. Use a direct file path reference instead.

#### [MODIFY] `skills/verification-before-completion/SKILL.md`

- Add `schedule` timer usage for long-running verification commands: set a one-shot timer when launching a build/test suite that might take more than a few minutes.

---

### Component 3: Cache-Optimized Subagent Definitions

Replace fill-in-the-blank prompt templates with `define_subagent` type definitions. Split each template into a **static system prompt** (frozen in context cache) and **dynamic runtime data** (passed per invocation).

#### Design Principle: Static/Dynamic Split

The Gemini context cache works on exact prefix matches. If the `system_prompt` in `define_subagent` changes between invocations (because dynamic data was baked in), the cache is invalidated. Therefore:

- **Static system_prompt:** Role identity, behavioral guidelines, review criteria, output format, escalation rules. Never changes between tasks.
- **Dynamic Prompt:** Task text, context, file paths, git SHAs, implementer reports. Changes every invocation.

#### Three Subagent Type Definitions

##### `implementer`

**Static system_prompt contents (from `implementer-prompt.md`):**
- Role: "You are an implementer subagent"
- TDD workflow requirements
- Self-review checklist (completeness, quality, discipline, testing)
- Escalation rules (DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT)
- Code organization principles (one responsibility per file, follow plan structure)
- "When you're in over your head" escalation guidance
- Report format specification

**Dynamic Prompt contents (per invocation):**
- Task N name and full text
- Scene-setting context (where this fits, dependencies)
- Working directory
- Any answers to prior questions

##### `spec-reviewer`

**Static system_prompt contents (from `spec-reviewer-prompt.md`):**
- Role: "You are a spec compliance reviewer"
- Adversarial stance: "Do not trust the implementer's report"
- Review methodology: check for missing requirements, extra/unneeded work, misunderstandings
- "Verify by reading code, not by trusting report"
- Output format: ✅ Spec compliant / ❌ Issues found with file:line references

**Dynamic Prompt contents (per invocation):**
- Full text of task requirements
- Implementer's report (what they claim they built)
- File paths to inspect

##### `code-reviewer`

**Static system_prompt contents (from `code-reviewer.md`):**
- Role: "You are a Senior Code Reviewer"
- Review criteria: plan alignment, code quality, architecture, testing, production readiness
- Calibration guidance: categorize by actual severity, acknowledge strengths
- Output format: Strengths → Issues (Critical/Important/Minor) → Recommendations → Assessment
- Additional checks for file responsibility, decomposition, file size growth

**Dynamic Prompt contents (per invocation):**
- Description of what was built
- Plan/requirements text
- BASE_SHA and HEAD_SHA for `git diff`

#### [MODIFY] `skills/subagent-driven-development/SKILL.md`

Rewrite to instruct the orchestrator to:
1. Call `define_subagent` for all three types at the start of plan execution.
2. Call `invoke_subagent` with `TypeName: "implementer"` per task (dynamic Prompt only).
3. Call `invoke_subagent` with `TypeName: "spec-reviewer"` after implementation.
4. Call `invoke_subagent` with `TypeName: "code-reviewer"` after spec review passes.

#### [REWRITE] `skills/subagent-driven-development/implementer-prompt.md`

Transform from fill-in-the-blank template to a `define_subagent` definition document:
- Section 1: Static system_prompt (copy verbatim into `define_subagent`)
- Section 2: Dynamic Prompt template (placeholders for task text, context, working directory)

#### [REWRITE] `skills/subagent-driven-development/spec-reviewer-prompt.md`

Same transformation as implementer.

#### [REWRITE] `skills/subagent-driven-development/code-quality-reviewer-prompt.md`

Merge into `code-reviewer` type. This file currently just says "use code-reviewer.md template" with extra checks. Those extra checks move into the `code-reviewer` static system_prompt.

#### [REWRITE] `skills/requesting-code-review/code-reviewer.md`

Transform from fill-in-the-blank template to `define_subagent` definition document. The static system_prompt is shared with `subagent-driven-development`'s code-reviewer.

#### Token Savings Estimate

Per task in a 5-task plan:
- 3 subagent invocations (implementer + spec-reviewer + code-reviewer)
- ~2,500 tokens of static system prompt per invocation = ~7,500 tokens/task
- Over 5 tasks = 37,500 tokens of repeated prompts
- With `define_subagent`: pay ~7,500 once
- **Net savings: ~30,000 tokens per 5-task plan**

---

### Component 4: Native Interactive UI

Replace text-based option menus with `ask_question` structured modals.

#### [MODIFY] `skills/finishing-a-development-branch/SKILL.md`

Replace the text-formatted 4-option menu (lines 68-91) with instruction to use `ask_question`:

```
ask_question(questions: [{
  question: "Implementation complete. What would you like to do?",
  options: [
    "Merge back to <base-branch> locally",
    "Push and create a Pull Request",
    "Keep the branch as-is (I'll handle it later)",
    "Discard this work"
  ],
  is_multi_select: false
}])
```

Similarly for the 3-option detached HEAD menu.

#### [MODIFY] `skills/brainstorming/SKILL.md`

Add explicit instruction: when presenting multiple-choice questions during brainstorming, use `ask_question` instead of typing numbered options in text. This provides a premium interactive modal.

#### [MODIFY] `skills/writing-plans/SKILL.md`

Replace the execution handoff text menu with `ask_question`. Since `executing-plans` is deleted, this simplifies to a confirmation: "Plan complete. Ready to execute with subagent-driven-development?"

---

### Component 5: Simplify Workspace Isolation

#### [MODIFY] `skills/using-git-worktrees/SKILL.md`

Reduce from 216 lines to ~50 lines. The new flow:

1. **Step 0: Detect existing isolation** — keep as-is (check `GIT_DIR` vs `GIT_COMMON`).
2. **Step 1: Create isolation** — for subagent tasks, use `Workspace: "branch"` parameter on `invoke_subagent`. For parent orchestrator feature branches, use `git checkout -b <branch>` directly (no manual worktree creation).
3. **Step 2: Project setup** — keep auto-detect logic (npm install, cargo build, etc.).
4. **Step 3: Verify clean baseline** — keep test verification.

Delete all of:
- Step 1b (git worktree fallback) — 50+ lines
- Directory selection priority logic — 20+ lines
- Safety verification for `.worktrees/` — 10+ lines
- Sandbox fallback — 5+ lines
- Global `~/.config/superpowers/worktrees/` legacy support — 10+ lines

---

### Component 6: Replace Visual Companion

#### [MODIFY] `skills/brainstorming/SKILL.md`

Replace the visual companion section (lines 147-164) with two-tool approach:

- **Mockups and wireframes:** Use `generate_image` to create visual mockups. Render inline with `![Mockup description](/path/to/image.png)` in artifacts.
- **Interactive selection:** Use `ask_question` with options for design choices.

This replaces the Node.js server (`scripts/server.cjs`), HTML templates, and the entire file-watching + event-polling loop.

#### [DELETE] `skills/brainstorming/visual-companion.md`

The 288-line visual companion guide for the browser-based server is no longer needed.

#### [DELETE] `skills/brainstorming/scripts/` (directory)

Server scripts, frame templates, and helper JS files.

---

### Component 7: Update Documentation and Tests

#### [MODIFY] `README.md`

- Remove all non-Antigravity installation instructions (Claude Code, Codex, Cursor, Gemini CLI, OpenCode, Copilot CLI, Factory Droid sections).
- Remove "What's different in this fork?" section — this is no longer a fork, it's its own project.
- Remove "Cross-platform" row from the fork differences table.
- Update skills library listing to remove `executing-plans`.
- Simplify contributing section (no longer needs to work across all coding agents).

#### [MODIFY] `GEMINI.md`

- Remove reference to `antigravity-tools.md` (deleted).
- Keep reference to `using-superpowers/SKILL.md`.

#### [DELETE] `AGENTS.md`

Contains only `CLAUDE.md` — no longer relevant.

#### [MODIFY] `CLAUDE.md`

Rewrite as `CONTRIBUTING.md` with Antigravity-specific contributor guidelines. Remove all Claude Code-specific references.

#### [MODIFY] `tests/antigravity/`

Update test suite:
- **[REWRITE/RENAME]** Rename `test-tool-mapping-accuracy.sh` to `test-skill-tool-purity.sh`. Instead of checking a mapping file, this script will statically analyze all skill files to assert:
  - No Claude Code/legacy tool names are referenced (`TodoWrite`, `Task tool`, `Skill tool`, `EnterWorktree`, `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `WebSearch`, `WebFetch`).
  - No legacy platform references or tool mapping files are referenced.
  - All referenced tools match the valid Antigravity 2.0 tool list.
- **[MODIFY]** Update `test-skill-triggering/run-all.sh` to remove `"executing-plans"` from the test array, and remove the `SHARED_PROMPTS_DIR` fallback (it will check `LOCAL_PROMPTS_DIR` exclusively).
- **[MODIFY]** Copy/migrate prompt files for `dispatching-parallel-agents.txt`, `requesting-code-review.txt`, `systematic-debugging.txt`, `test-driven-development.txt`, and `writing-plans.txt` from `tests/skill-triggering/prompts/` to `tests/antigravity/test-skill-triggering/prompts/` before deleting the source folder.
- **[MODIFY]** Update `test-subagent-dispatch.sh` and `test-worktree-workspace.sh` to assert and verify:
  - `define_subagent` is used for `implementer`/`spec-reviewer`/`code-reviewer` types.
  - `invoke_subagent` references custom defined types, not `"self"`.
  - `ask_question` is invoked for interactive menus.
  - Workspace isolation uses the `Workspace: "branch"` parameter.

#### [DELETE] `tests/explicit-skill-requests/`
#### [DELETE] `tests/skill-triggering/` (after copying prompt files)
#### [DELETE] `tests/subagent-driven-dev/`
#### [DELETE] `tests/brainstorm-server/`

Claude Code and cross-platform test suites. Replace with Antigravity-specific equivalents in `tests/antigravity/`.

---

### Component 8: Cleanup Miscellaneous

#### [MODIFY] `skills/dispatching-parallel-agents/SKILL.md`

- Replace `Task(...)` Claude Code syntax (lines 68-74) with `invoke_subagent` with `Subagents` array showing parallel dispatch.
- Update example to use native tool names.

#### [MODIFY] `skills/receiving-code-review/SKILL.md`

- Review for any CC-specific references and replace with native equivalents.

#### [MODIFY] `skills/finishing-a-development-branch/SKILL.md`

- Replace worktree cleanup logic to account for simplified `using-git-worktrees` (no more `.worktrees/` directory convention — subagents use `Workspace: "branch"` which the platform cleans up).

#### [MODIFY] `gemini-extension.json`

Keep as-is. This is the Antigravity 2.0 plugin discovery manifest.

#### [MODIFY] `plugin.json`

Bump version to `6.0.0` to mark the Antigravity-native fork.

---

## Verification Plan

### Automated Tests

```bash
# Run updated Antigravity test suite
cd tests/antigravity && bash test-plugin-discovery.sh
cd tests/antigravity && bash test-skill-tool-purity.sh
cd tests/antigravity && bash test-subagent-dispatch.sh
cd tests/antigravity && bash test-worktree-workspace.sh
cd tests/antigravity/test-skill-triggering && bash run-all.sh
```

### Content Verification

```bash
# Verify no Claude Code tool names remain in skills
grep -r "TodoWrite\|Task tool\|Skill tool\|EnterWorktree" skills/ && echo "FAIL: Legacy tool names found" || echo "PASS"

# Verify no deleted platform references remain
grep -r "Claude Code\|Codex\|Copilot\|Cursor\|OpenCode\|Factory Droid\|Gemini CLI" skills/ && echo "FAIL: Legacy platform references found" || echo "PASS"

# Verify no tool mapping files are referenced
grep -r "antigravity-tools\|copilot-tools\|codex-tools\|gemini-tools" skills/ && echo "FAIL: Tool mapping references found" || echo "PASS"
```

### Manual Verification

1. Start a fresh Antigravity session with the refactored plugin installed.
2. Type: "Let's make a react todo list"
3. Verify: brainstorming skill triggers automatically with `ask_question` for choices.
4. Execute a 2-task plan and verify: `define_subagent` is called for implementer/spec-reviewer/code-reviewer at start, `invoke_subagent` uses custom types, task tracking uses `task.md` artifact.
