---
name: skill-manager
description: The Skill Manager for AI Agents. Use this to find, install, sync, and manage skills.
---

# Agent Skill Manager (ASM)

This is your **primary tool** for managing your own capabilities.

## 🛠️ Capabilities

### 1. 🔍 Find Skills
**Usage**: Discover capabilities you don't have.
**Constraint**: **ONLY** list results. Do **NOT** install anything unless explicitly ordered by the user.
**Command**:
```bash
npx skills find <search_query>
```

### 2. ⬇️ Install Skill
**Usage**: Install a skill explicitly requested by the user.
**Decision Logic**:
- **Global**: General-purpose tools ($HOME).
- **Project**: Workspace-specific tools (Current Dir).
**Command**:
```bash
python3 scripts/install_skill.py <skill_source>
```

### 3. 📋 List & Check Skills
**Usage**: Check current capabilities and sync status.
**Command**:
```bash
python3 scripts/list_skills.py
```

### 4. 🔄 Sync Skill
**Usage**: Fix missing tools or sync to a new agent environment.
**Command**:
```bash
python3 scripts/sync_skill.py <skill_name>
```

### 5. 🆙 Update Skills
**Usage**: Update installed skills to latest versions.
**Interactive Mode**: Run without arguments to see the TUI menu.
**Command**:
```bash
python3 scripts/update_skills.py
```

### 6. 🗑️ Uninstall Skill
**Usage**: Remove a skill and clean up configurations.
**Interactive Mode (Preferred)**: Run **WITHOUT** arguments to enter a TUI-based selection menu across scopes.
**Command**:
```bash
python3 scripts/uninstall_skill.py
```

## 🧠 Agent Protocol

1.  **Strictly Non-Autonomous Installation**: After running `npx skills find`, you must show the list to the user and wait. **Proactive installation is strictly forbidden.**
2.  **Interaction First**: If the user gives a generic command like "uninstall skills" or "update tools", **DO NOT** ask for names or run `list_skills` first. Directly launch the corresponding script without arguments to provide the user with a TUI selection menu.
3.  **Explicit Consent for Scope**: Never assume a skill should be Global. Always ask the user: "Which scope (Global or Project) should I use?"
4.  **No Ghost Actions**: All install, uninstall, and sync actions must be in response to direct user commands.
5.  **Verification**: Always use `python3 scripts/list_skills.py` to confirm the current state before making suggestions.
