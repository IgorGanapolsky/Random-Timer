---
description: Set up InsForge backend and Antigravity AgentKit 2.0
---
This workflow sets up the InsForge backend and integrates Antigravity AgentKit to automate full-stack feature development.

1. **Install and set up tools**  
   - Install Antigravity, sign in with your Google account, and create/open the project directory.
   - Create a free InsForge account, set up a new project in your region, and acquire the CLI link command.

2. **Link InsForge to Antigravity**
   - Open the Antigravity terminal and run the `npx` InsForge CLI command to link the local project.
// turbo
   - Connect the InsForge agent via MCP by running the provided connection command in the Antigravity terminal.

3. **Install Antigravity AgentKit 2.0**
// turbo
   - Run the AgentKit install command (e.g., `npm install -g agentkit` or local install) in the project root.
// turbo
   - Initialize AgentKit (`agit init` or equivalent) to wire workflows, skills, and rule sets (`AGENTS.md`) into the current agent configuration.

4. **Define your product specs**
   - Run `/brainstorm` to define product details, constraints, and backend requirements (Auth, DB, Storage).
   - Let the agent read `Brainstorm MD` and generate explicit specs.

5. **Provision Backend Autonomously**
   - Trigger the backend setup prompt via MCP to spin up the Auth, Database Schema, and Storage buckets.
   - Verify in the InsForge console that all backend services are "healthy".

6. **Generate the Frontend and UX**
   - Execute the paired frontend prompt to scaffold UI and design systems.
   - Use AgentKit’s Visual/UX Specialist models to iterate on landing pages and core components.

7. **Use Dev Workflows**
   - Use commands like `/create`, `/debug`, `/deploy`, and `/enhance` for ongoing iteration without fully manual edits.

8. **Wire in LLM-powered features**
   - Enable the Model Gateway in InsForge (e.g., Gemini 1.5 Pro/Flash).
   - Ask the agent to integrate GenAI features (like dynamic training routines) and verify logs.

9. **Live Backend Commands**
   - Stream backend schema updates via CLI (e.g., "add profile image column to users table").
   - Monitor data ingestion (like `timer_completed` events) live in the InsForge dashboard.

10. **Deploy and Iterate**
   - Run the deploy command ("deploy my app to InsForge").
   - Configure custom domains, test Auth providers, and maintain infrastructure via AgentKit.
