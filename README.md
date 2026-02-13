# ⚡️ Agent Skill Manager

[🇨🇳 中文](./README_CN.md) | [🇺🇸 English](./README.md)

> **Unified Management for Your Agent's Skills.**
>
> Centralize `skills.sh` ecosystem and custom Git skills in one place, and sync them to all your AI agents.

---

## 🤖 What is this?

This is a **Unified Skill Manager** that brings two skill worlds together:

1.  **skills.sh Ecosystem**: Skills installed via `npx skills`.
2.  **Manual/Git Skills**: Private or custom skills installed via Git/Local paths.

It centralizes **ALL** capabilities into `~/.agents/skills/` and automatically synchronizes them to **Claude**, **Gemini**, **Cursor**, and more.

## 🚀 Key Value

*   **Unified Home**: No more scattered tools.
    *   **Global**: `~/.agents/skills/` (available to all projects).
    *   **Project**: `./.agents/skills/` (isolated to current project).
*   **Universal Sync**: Install once, available everywhere (Claude, Gemini, Cursor, Trae, Replit, etc.).

## ⚡️ What can you manage?

Bring ANY tool to your agent's fingertips:

*   **From Community (npx)**: Install `browser-skill` to let your agent search the web.
*   **From Work (Git)**: Clone your private `internal-api-skill` for safe database access.
*   **From Local (Path)**: Link your local scripts for development.

## ⚠️ Prerequisites

Before installing, ensure your environment meets these requirements:

- **OS**: macOS or Linux (Windows/WSL support is experimental).
- **Python**: 3.9 or higher (uses `pathlib` features).
- **Node.js**: Required for the `skills.sh` ecosystem (`npx`).
- **Git**: Required for cloning skills from repositories.

## 📦 Installation

One line to setup the bridge.

```bash
git clone https://github.com/your-username/skill-manager.git ~/.agents/skills/skill-manager && chmod +x ~/.agents/skills/skill-manager/scripts/*.py
```

## 📖 Usage Guide

### 🗣️ Trigger Examples (Natural Language)

Since this is an Agent Skill, you can just ask your agent:

*   "Find a skill for reading PDF files."
*   "Install the `browser-skill` (it will auto-detect context)."
*   "List all my installed skills."
*   "Sync my skills now."

### 🤖 For Agents (The "Auto" Mode)

If you are an AI Agent reading this: **You have new skills available.**
Check `SKILL.md` for detailed triggers.

*   To find a tool: Run `npx skills find <intent>`
*   To install a tool: Run `npx skills add <package> -g -y`

### 👤 For Humans (Management)

**1. Install a new Skill (Recommended Unified Command)**
Handles Community Registry, Git URLs, and Local paths. It prompts for scope ONLY when necessary.
```bash
# Handled automatically: Registry, Git, or Local
python3 scripts/install_skill.py <skill_name_or_url>

# Examples:
python3 scripts/install_skill.py browser-skill      # Community
python3 scripts/install_skill.py https://github... # Git
```

> 💡 **Smart Git Install**: When installing from a GitHub URL, the script automatically analyzes the repo structure. If the repo contains multiple skills in subdirectories, you'll be prompted to select which to install. If no `SKILL.md` is found, the README is printed for reference.

**3. Sync & Update**
```bash
# Interactive TUI (Select skills to update)
python3 scripts/update_skills.py

# Smart Update specified skill
# Only prompts for scope if the skill exists in both Global & Project.
python3 scripts/update_skills.py <skill-name>

# Auto-Update All
python3 scripts/update_skills.py --all --npx
```

**4. Check what your Agent can do**
```bash
python3 scripts/list_skills.py
```

**5. Clean Uninstall**
```bash
# Removes from Central Repo, Registry (if npx), and all synced agents
python3 scripts/uninstall_skill.py <skill-name>
```

## 🔌 Supported Agents

| Platform | Global Path | Project Path |
| :--- | :--- | :--- |
| **AdaL** | `~/.adal/skills` | `.adal/skills` |
| **Amp** | `~/.config/agents/skills` | `.agents/skills` |
| **Antigravity** | `~/.gemini/antigravity/skills` | `.agent/skills` |
| **Augment** | `~/.augment/skills` | `.augment/skills` |
| **Claude Code** | `~/.claude/skills` | `.claude/skills` |
| **Cline** | `~/.cline/skills` | `.cline/skills` |
| **CodeBuddy** | `~/.codebuddy/skills` | `.codebuddy/skills` |
| **Codex** | `~/.codex/skills` | `.agents/skills` |
| **Command Code** | `~/.commandcode/skills` | `.commandcode/skills` |
| **Continue** | `~/.continue/skills` | `.continue/skills` |
| **Crush** | `~/.config/crush/skills` | `.crush/skills` |
| **Cursor** | `~/.cursor/skills` | `.cursor/skills` |
| **Droid** | `~/.factory/skills` | `.factory/skills` |
| **Gemini CLI** | `~/.gemini/skills` | `.agents/skills` |
| **GitHub Copilot** | `~/.copilot/skills` | `.agents/skills` |
| **Goose** | `~/.config/goose/skills` | `.goose/skills` |
| **Junie** | `~/.junie/skills` | `.junie/skills` |
| **Kilo Code** | `~/.kilocode/skills` | `.kilocode/skills` |
| **Kimi Code CLI** | `~/.config/agents/skills` | `.agents/skills` |
| **Kiro CLI** | `~/.kiro/skills` | `.kiro/skills` |
| **Kode** | `~/.kode/skills` | `.kode/skills` |
| **MCPJam** | `~/.mcpjam/skills` | `.mcpjam/skills` |
| **Mistral Vibe** | `~/.vibe/skills` | `.vibe/skills` |
| **Mux** | `~/.mux/skills` | `.mux/skills` |
| **Neovate** | `~/.neovate/skills` | `.neovate/skills` |
| **OpenClaw** | `~/.moltbot/skills` | `skills` |
| **OpenCode** | `~/.config/opencode/skills` | `.agents/skills` |
| **OpenHands** | `~/.openhands/skills` | `.openhands/skills` |
| **Pi** | `~/.pi/agent/skills` | `.pi/skills` |
| **Pochi** | `~/.pochi/skills` | `.pochi/skills` |
| **Qoder** | `~/.qoder/skills` | `.qoder/skills` |
| **Qwen Code** | `~/.qwen/skills` | `.qwen/skills` |
| **Replit** | `~/.config/agents/skills` | `.agents/skills` |
| **Roo Code** | `~/.roo/skills` | `.roo/skills` |
| **Trae** | `~/.trae/skills` | `.trae/skills` |
| **Trae CN** | `~/.trae-cn/skills` | `.trae/skills` |
| **Windsurf** | `~/.codeium/windsurf/skills` | `.windsurf/skills` |
| **Zencoder** | `~/.zencoder/skills` | `.zencoder/skills` |
| **iFlow CLI** | `~/.iflow/skills` | `.iflow/skills` |

## ❓ Troubleshooting

**Q: My Agent still says it can't do X.**
A: Ensure you selected the correct scope in the TUI menu, or run `python3 scripts/list_skills.py` to check the detailed sync status and repository paths.

**Q: How do I remove a skill?**
A: `python3 scripts/uninstall_skill.py <skill-name>`. It will automatically trigger `npx skills remove` if it's a registry skill.
