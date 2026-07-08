# SAD Alignment Examples

Worked examples of the SkillWeave Iterative Skill-Aware Decomposition (SAD) pipeline applied to real user requests.

Each example shows:
1. The raw user request
2. Initial (naive) decomposition
3. SAD alignment check against `skill-index.json`
4. Re-decomposition where needed
5. Final execution plan with DAG order

---

## Example 1: "Add dark mode to my React app"

### Initial Decomposition
1. Set up dark mode CSS system
2. Add toggle button component
3. Make it persist across sessions
4. Write tests

### SAD Alignment Check

| Sub-task | Trigger match | Skill | Aligned? |
|----------|--------------|-------|----------|
| Set up dark mode CSS system | "design", "new feature" | `brainstorming` | ✓ |
| Add toggle button | "implement", "code" | `test-driven-development` | ✓ |
| Make it persist | ← merge with above (same task) | `test-driven-development` | ✓ |
| Write tests | ← already part of TDD | `test-driven-development` | ✓ (merged) |

DA = 3/3 = 1.0 ✓ (after merging "add toggle" + "persist" + "write tests" into one TDD cycle)

Missing: verification and planning steps were implicit. SAD adds them from the DAG.

### Final Execution Plan (DAG order)
```
brainstorming → writing-plans → test-driven-development → verification-before-completion
```

---

## Example 2: "Fix the login bug"

### Initial Decomposition
1. Find the bug
2. Fix the bug

### SAD Alignment Check

| Sub-task | Trigger match | Skill | Aligned? |
|----------|--------------|-------|----------|
| Find the bug | "bug", "debug", "investigate" | `systematic-debugging` | ✓ |
| Fix the bug | "fix", "implement" | `test-driven-development` | ✓ |

DA = 2/2 = 1.0 ✓

### Final Execution Plan
```
systematic-debugging → test-driven-development → verification-before-completion
```

---

## Example 3: "Build a REST API with authentication"

### Initial Decomposition (naive)
1. Set up Express/FastAPI
2. Add auth
3. Add endpoints
4. Test everything

### SAD Alignment Check — First Iteration

| Sub-task | Check | Result |
|----------|-------|--------|
| Set up Express | "implement", "setup" | `test-driven-development` — but wait, no design yet | ⚠ partial |
| Add auth | "add feature" | `brainstorming` needed first | ✗ out of order |
| Add endpoints | "implement" | `test-driven-development` | ✓ |
| Test everything | "verify" | `verification-before-completion` | ✓ |

DA = 2/4 = 0.5 < 0.8 threshold → **RE-DECOMPOSE**

### SAD Re-Decomposition

| Sub-task | Trigger match | Skill | Aligned? |
|----------|--------------|-------|----------|
| Design the API structure and auth approach | "design", "new feature" | `brainstorming` | ✓ |
| Plan the implementation tasks | "implementation plan" | `writing-plans` | ✓ |
| Implement auth + endpoints with TDD | "implement", "TDD", "test first" | `test-driven-development` | ✓ |
| Verify the API | "verify", "validate" | `verification-before-completion` | ✓ |

DA = 4/4 = 1.0 ✓

### Final Execution Plan
```
brainstorming → writing-plans → test-driven-development → verification-before-completion → finishing-a-development-branch
```

---

## Example 4: "I have 3 independent research tasks to do simultaneously"

### Initial Decomposition
1. Research task A
2. Research task B
3. Research task C

### SAD Alignment Check

| Sub-task | Trigger match | Skill | Aligned? |
|----------|--------------|-------|----------|
| Research A | "parallel", "simultaneously" | `dispatching-parallel-agents` | ✓ |
| Research B | ← merge into parallel dispatch | `dispatching-parallel-agents` | ✓ (merged) |
| Research C | ← merge into parallel dispatch | `dispatching-parallel-agents` | ✓ (merged) |

DA = 1/1 = 1.0 ✓ (all 3 research tasks collapsed into one parallel dispatch)

### Final Execution Plan
```
dispatching-parallel-agents (running A, B, C simultaneously)
```

---

## Example 5: "My CI/CD pipeline is broken, the tests are failing"

### Initial Decomposition (naive, common bad pattern)
1. Look at the errors
2. Fix the errors

### SAD Alignment Check — First Iteration

| Sub-task | Check | Result |
|----------|-------|--------|
| Look at the errors | Too vague | No trigger match | ✗ |
| Fix the errors | "fix" | `test-driven-development` — but without root cause first | ⚠ wrong order |

DA = 0/2 = 0.0 → **RE-DECOMPOSE** (SAD critical feedback)

### SAD Re-Decomposition (Iteration 2)

| Sub-task | Trigger match | Skill | Aligned? |
|----------|--------------|-------|----------|
| Investigate root cause of CI failures | "bug", "error", "failure", "build failing", "investigate" | `systematic-debugging` | ✓ |
| Fix using TDD to prevent regression | "bug fix", "TDD" | `test-driven-development` | ✓ |
| Verify CI passes | "verify", "check" | `verification-before-completion` | ✓ |

DA = 3/3 = 1.0 ✓

**This is the key SAD improvement:** Without SAD, the agent jumps to "fix it" (wrong skill order). SAD's feedback loop forces "investigate first" → correct skill ordering.

### Final Execution Plan
```
systematic-debugging → test-driven-development → verification-before-completion
```

---

## SAD Anti-Patterns to Avoid

### Anti-Pattern 1: Decomposing into tool-level steps (too granular)
❌ "Read file X", "Search for pattern Y", "Write to file Z"
These are agent actions, not skill-level sub-tasks.
✓ Keep sub-tasks at skill granularity: "Debug the failing test" → `systematic-debugging`

### Anti-Pattern 2: Decomposing into vague categories (too coarse)
❌ "Fix the app", "Make it work"
These don't map to any skill trigger.
✓ Re-decompose to atomic sub-tasks with clear verbs.

### Anti-Pattern 3: Skipping dependency ordering
❌ Jumping to implementation without brainstorming
✓ The DAG ensures brainstorming → writing-plans → executing-plans order is enforced.

### Anti-Pattern 4: Loading all skills "just in case"
❌ Loading all 15 SKILL.md files at session start
✓ Load only skill-index.json, then load matched SKILL.md files on demand.
