# Code Style

Coding standards and practices for agentic development. Ensures module quality, traceable specifications, and reliable error handling.

## Purpose

Establish consistent rules for module creation, testing, and error reporting so that:

- Module specifications are preserved through parallel documentation.
- Code quality is verified via specification-based tests.
- Environment mismatches are diagnosed systematically.
- Tool errors are handled with user confirmation.
- Dependency additions are reported and approved by the user.
- Edits are kept small and targeted.
- Files are read before any edit is applied.

## Rules

### Documentation-First Module Creation

- Create documentation alongside any new module. Do not defer documentation until after implementation.
- Record the following in the documentation:
  - Purpose and responsibilities of the module.
  - Public interfaces: functions, classes, and their parameters/return values.
  - Dependencies and expected usage patterns.
  - Rationale for key design decisions.
- Place documentation near the module (e.g., `module_name.md` next to `module_name.py`).
- When using an existing module, read its documentation first and follow its documented interface. Never assume behavior that is not documented.

### Specification-Based Testing

- Every module must have a corresponding test file.
- Write tests that directly reflect the module's documented specifications.
- Ensure tests cover:
  - Normal (happy-path) cases.
  - Edge cases and boundary values.
  - Error conditions and expected failure modes.
- Run tests after making changes to the module and confirm they all pass before considering the module complete.

### Environment-Aware Error Handling

- The development environment and the user's execution environment may differ (OS, libraries, versions, paths).
- When a user reports an error, ask for the following before attempting a fix:
  - Operating system and version.
  - Interpreter / runtime and its version.
  - Relevant dependency versions.
  - The exact command or input that triggered the error.
  - The full error message and stack trace.
- Do not assume a fix based on development-only behavior.

### Dependency Addition

- When adding a new external library or dependency, inform the user of its name and purpose.
- Obtain user approval before adding the dependency.
- Do not increase dependencies unnecessarily.

### Tool Error Confirmation

- When a tool call fails (e.g., shell command, file operation, external API), do not silently retry or guess.
- Always confirm the following with the user:
  - What the tool was attempting.
  - The error message received.
  - The intended next action (e.g., retry, alternative tool, manual intervention).
- Proceed only after receiving user confirmation.

### Small, Targeted Edits

- Keep changes small and targeted. Prefer precise replacements over replacing entire functions or files.
- Do not blindly replace large blocks of code. Replace only the specific content that needs to change.
- If a rule or skill references another, keep paths relative to the repo root.

### Read Before Edit

- Always read a file before editing it.
- Verify the file's current content matches your expectations before applying changes.
- Use the exact content from the read output as `original_content` in replacements — do not invent or modify it.

## Steps

1. **Identify** the module or task you are working on.
2. **Create or update** the corresponding documentation before or alongside implementation.
3. **Write tests** derived directly from the documented specifications.
4. **Run tests** and confirm all pass.
5. If the user reports an error, **collect environment details** using the checklist above.
6. If a tool fails, **report the error to the user** and await confirmation before proceeding.

## Output

- Documented module specification (`.md` file).
- Test file covering the documented specifications.
- Error reports that include full context (environment details, commands, messages).
- Tool error confirmations logged before any retry or alternative approach.
