# WicdPico Collaborative Refactoring Workflow & AI Interaction Guidelines

## Task Management & Chat Commands
- Use short, simple tasks.
- Use `@<filename>` to reference files.
- `/chat` ends the current chat, saves context, and starts a new chat.
- To refresh context, update `context.md`, then use `/clear` and tell the assistant to read `context.md`.

## Collaborative Refactoring Checklist

### Phase 1: Strategy & Prompt Engineering (Chat)
1. **Target Selection & Analysis**
   - Select a module to refactor and provide its code.
   - Identify all configurable values (I2C addresses, magic numbers, thresholds, etc.).
2. **settings.toml Structure Design**
   - Design a clear, consistent TOML table for each module.
   - Example:
     ```toml
     [module_bh1750]
     i2c_address = "0x23"
     measurement_mode = "high_res_2"
     ```
3. **Module & Foundation Modification Plan**
   - Modify the module’s `__init__` to accept a config dictionary.
   - Update main files (`code_*.py`) to load and pass config from `settings.toml`.
4. **Optimized CLI Prompt**
   - Once the plan is agreed, synthesize a single prompt for the Gemini CLI:
     - Modify the target module to accept config.
     - Update main file(s) to load and pass config.
     - Provide new settings.toml text.
   - Advise if `/clear` is needed before starting a new task.

### Phase 2: Execution & Validation (Terminal)
- Run the provided CLI command.
- Update `settings.toml` with the new config block.
- Test the application to confirm correct module initialization and behavior.

### Phase 3: Context Save (Persistent Memory)
- After successful refactoring and validation, update `context.md` with a concise summary.
- The assistant will prompt:  
  `"Now is a good time to update your context.md. Here is the summary to add:"`
- This creates a permanent record for future sessions.

## Codebase Interaction Principles

### Existing Code First
- **Always examine the codebase** (using Read, Grep, or Glob tools) before writing new code.
- **Never assume code structure**—verify patterns, class names, method signatures, and conventions.

### Real Features Only
- **Never create placeholder, mock, or demo code.**
- Only implement real, functional features.
- If interim non-functional steps are needed, ask for permission and explain why.

### Reuse Existing Code Mandate
- Before writing new code:
  1. Check if existing code already does the job.
  2. Look for existing patterns, functions, or modules.
  3. Use existing infrastructure and frameworks.
  4. Only write new code if existing code cannot be adapted or extended.
- If existing code does 80% of what's needed, extend or modify it.
- Prefer established patterns over new ones.
- When in doubt, ask: "Does something already exist that does this job?" If yes, use it.

---

**This context ensures efficient, disciplined, and collaborative project management and AI interaction.**