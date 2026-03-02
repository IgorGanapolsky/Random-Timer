# Agent-Model Matching

## Task Categories & Fallback Chains

Match the right "brain" to the right task to maximize effectiveness, speed, and cost-efficiency.

| Category | Description | Primary Model | Fallback 1 | Fallback 2 |
| :--- | :--- | :--- | :--- | :--- |
| **UltraBrain** | Deep architectural logic, multi-file reasoning, complex bug hunting | `claude-3-5-sonnet` | `gemini-1.5-pro` | `gpt-4o` |
| **Deep** | Large-scale refactoring, complex feature implementation | `claude-3-opus` | `gpt-4o` | `gemini-1.5-pro` |
| **Quick** | Codebase search, file analysis, scaffolding, simple tests | `gemini-1.5-flash` | `claude-3-haiku` | `gpt-4o-mini` |
| **Visual** | UI/UX implementation, layout debugging, multimodal tasks | `gemini-1.5-pro` | `gpt-4o` | `claude-3-5-sonnet` |

## Brain Personalities & Optimization

### Claude-family (Sonnet, Opus, Haiku)
- **Strengths**: Mechanics-driven prompts, multi-step checklists, structured JSON/YAML output.
- **Prompting Style**: Use detailed requirements, explicit constraints, and step-by-step instructions.

### GPT-family (GPT-4o, GPT-4o-mini)
- **Strengths**: Goal-oriented exploration, autonomous problem solving, principle-driven reasoning.
- **Prompting Style**: Focus on the *intent* and *outcome* rather than the specific mechanics.

### Gemini-family (Pro, Flash)
- **Strengths**: Massive context windows, multimodal (image/video) reasoning, rapid search.
- **Prompting Style**: Provide all relevant files as context (up to 2M tokens) and ask for global analysis.

## Resolution Logic

When an agent is invoked via the `Task` tool:
1. **Check Agent Category**: Refer to the agent's frontmatter (e.g., `category: Quick`).
2. **Resolve Model**: Use the Primary Model for that category.
3. **Handle Availability**: If the Primary is hitting rate limits or unavailable, proceed down the Fallback Chain.
4. **Environment Check**: Prioritize models where the local environment has active API keys/provider access.
