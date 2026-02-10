---
name: skill-manager
description: AI Skill Manager. Find, install, sync, and manage AI Skills (MCP tools) for your agent. Supports the skills.sh ecosystem (npx skills) and Git/Local installations.
---

# Agent Skill Manager (ASM)

This is your **core skill management tool**. When you need new capabilities or tools to complete a task, **you MUST use this skill first**.

## 🎯 Trigger Phrases
- User says "I need a tool to do X"
- User says "Is there a skill for handling PDFs?"
- User says "Install a browser skill for me"
- User says "List installed skills"
- User says "Sync my skills"
- When you are stuck and wonder "Is there an existing skill that can solve this?"

## 🚀 Core Commands

Choose the most appropriate command based on the scenario.

### 1. 🔍 Find Skills
**This is the FIRST step**. Always search the `skills.sh` registry first (contains many ready-to-use tools):
```bash
npx skills find <your_keywords>
```
*Examples: `npx skills find browser`, `npx skills find pdf`, `npx skills find linear`*

### 2. ⬇️ Install Skills

#### Plan A: Install from skills.sh (Recommended)
If `npx skills find` returns a suitable package (e.g., `owner/pkg`):
```bash
# IMPORTANT: Must use -g for global availability, -y for auto-confirmation
npx skills add <owner/pkg> -g -y
```

#### Plan B: Install from Git / Local
- **Global Install** (default, for generic tools):
  ```bash
  python3 scripts/install_skill.py <URL_or_Path>
  # or explicitly
  python3 scripts/install_skill.py <URL_or_Path> --scope global
  ```
- **Project Install** (for project-specific tools):
  ```bash
  python3 scripts/install_skill.py <URL_or_Path> --scope project
  ```

### 3. 📋 List Installed Skills
See what tools are available and their **Sync Status** (supports Global and Project scopes):
```bash
python3 scripts/list_synced.py
```

### 4. 🗑️ Uninstall Skills
Unified uninstallation entry point (handles both npx and git installs, cleans up symlinks across all platforms, supports Global/Project selection):
```bash
python3 scripts/uninstall_skill.py <skill-name>
```

### 5. 🔄 Update/Sync Skills
```bash
# Interactive update menu for both Global and Project skills
python3 scripts/update_skills.py
```

## 💡 Best Practices for Agents
1.  **Search First**: When facing unknown requirements, use `npx skills find` to search first.
2.  **Global Install**: For general-purpose tools (like browser, PDF tools), ALWAYS use `-g` (for npx) or default install (for python) to ensure the Skill is available to ALL Projects.
3.  **Verify Installation**: After installation, run `python3 scripts/list_synced.py` to confirm the Skill is successfully synced to the current environment (e.g., Antigravity/Gemini).

---

## 📂 Directory Structure Reference
-   **npx skills**: Installed in `~/.agents/skills/` (Global)
-   **Git skills**: Cloned to `~/.agents/skills/` and symlinked to platforms
-   **Platform Sync Paths**:
    -   **Global**: `~/.agents/skills/`
    -   **Project**: `./.agents/skills/`
    -   **Supported Platforms**: Claude Code, Antigravity, Gemini CLI, Cursor, GitHub Copilot, OpenAI Codex, Amp, Kimi Code CLI, Replit, Augment, OpenClaw, Cline, CodeBuddy, Command Code, Continue, Crush, Droid, Goose, Junie, iFlow, Kilo, Kiro, Kode, MCPJam, Mistral Vibe, Mux, OpenCode, OpenHands, Pi, Qoder, Qwen, Roo Code, Trae, Windsurf, Zencoder, Neovate, Pochi, AdaL...

This tool automatically handles all path mappings. You only need to focus on the commands in `scripts/`.
