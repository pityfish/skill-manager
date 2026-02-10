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

*   **Unified Home**: No more scattered tools. Whether it's from `npm` or `git`, it lives in `~/.agents/skills/`.
*   **Universal Sync**: Install once, available everywhere (Claude, Gemini, Antigravity, Cursor).
*   **Smart Management**: Auto-detects updates (`npx skills update` vs `git pull`).


## ⚡️ What can you manage?

Bring ANY tool to your agent's fingertips:

*   **From Community (npx)**: Install `browser-skill` to let your agent search the web.
*   **From Work (Git)**: Clone your private `internal-api-skill` for safe database access.
*   **From Local (Path)**: Link your local scripts for development.

## 📦 Installation

One line to setup the bridge.

```bash
git clone https://github.com/your-username/skill-manager.git ~/.agents/skills/skill-manager && chmod +x ~/.agents/skills/skill-manager/scripts/*.py
```

## 📖 Usage Guide

### 🗣️ Trigger Examples (Natural Language)

Since this is an Agent Skill, you can just ask your agent:

*   "Find a skill for reading PDF files."
*   "Install the `browser-skill` globally."
*   "List all my installed skills."
*   "Sync my skills now."
*   "I need a tool to manage my calendar, is there one?"

### 🤖 For Agents (The "Auto" Mode)

If you are an AI Agent reading this: **You have new skills available.**
Check `SKILL.md` for detailed triggers.

*   To find a tool: Run `npx skills find <intent>`
*   To install a tool: Run `npx skills add <package> -g -y`

### 👤 For Humans (Management)

**1. Install a new Skill (from Community)**
```bash
npx skills add browser-skill -g -y
```

**2. Install a new Skill (from Git)**
```bash
python3 scripts/install_skill.py https://github.com/user/awesome-tool.git
```

**3. Sync & Update**
```bash
python3 scripts/update_skills.py
```

**4. Check what your Agent can do**
```bash
python3 scripts/list_synced.py
```

## 🔌 Supported Agents

| Agent | Status | Path |
| :--- | :--- | :--- |
| **Claude Code** | ✅ Auto-Sync | `~/.claude/skills` |
| **Google Antigravity** | ✅ Auto-Sync | `~/.gemini/antigravity/skills` |
| **Gemini CLI** | ✅ Auto-Sync | `~/.gemini/skills` |
| **Cursor** | ✅ Auto-Sync | `~/.cursor/skills` |
| **GitHub Copilot** | ✅ Auto-Sync | `~/.copilot/skills` |
| **OpenAI Codex** | ✅ Auto-Sync | `~/.codex/skills` |

## ❓ Troubleshooting

**Q: My Agent still says it can't do X.**
A: Make sure you installed the skill with `-g` (global) or run `python3 scripts/install_skill.py` to ensure it's synced to `~/.gemini/antigravity/skills` (or your specific agent path).

**Q: How do I remove a skill?**
A: `python3 scripts/uninstall_skill.py <skill-name>`
