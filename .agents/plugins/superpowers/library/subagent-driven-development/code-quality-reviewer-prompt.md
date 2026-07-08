# Code Quality Reviewer

For subagent-driven-development, code quality review uses the `code-reviewer` subagent type.

The code-reviewer's static system prompt includes an "Additional Checks (Subagent-Driven Development)" section with the extra criteria for file responsibility, decomposition, and file size growth.

**Dispatch after spec compliance review passes:**

```
invoke_subagent(
  TypeName: "code-reviewer",
  Role: "Code quality reviewer for Task N",
  Prompt: <fill from code-reviewer.md dynamic template>
)
```
