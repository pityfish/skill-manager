---
name: skill-manager
description: Unified Agent Capability Manager. Use this skill to: 1) AUDIT and LIST your installed tools/capabilities. 2) FIND and INSTALL new skills (npx/Git/Local) to expand your toolset. 3) SYNC, UPDATE, or UNINSTALL existing skills across Global/Project scopes. Always use this first for self-correction or when you lack a required tool.
---

# Agent Skill Manager (ASM)

This is your **primary hub** for managing, auditing, and expanding your own functional capabilities. Whenever you or the user needs to know what tools are installed or want to add/remove a "skill", use this tool.

## 🛠️ Capabilities

### 1. 🔍 Find Skills
**Usage**: Discover capabilities you don't have.
**Constraint**: **ONLY** list results. Do **NOT** install anything unless explicitly ordered by the user.
**Command**:
```bash
npx skills find <search_query>
```

### 2. ⬇️ Install Skill
**Usage**: Install a skill explicitly requested by the user from any source (Registry name, Git URL, or Local Path).
**Constraint**: You **MUST** use the following script for **ALL** installation tasks. **NEITHER** use `npx skills add` directly **NOR** assume the installation scope yourself.

**Mandatory Command**:
```bash
python3 scripts/install_skill.py <skill_source>
```
*Note: This script will delegate to `npx` internally if needed and will handle the TUI scope prompt automatically.*

### 3. 📋 List & Check Skills
**Usage**: List all installed skills, check current capabilities, and verify sync status.
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
2.  **No Direct NPX Calls**: You **MUST NOT** call `npx skills add` or `npx skills remove` directly. Use the provided Python scripts (`install_skill.py`, `uninstall_skill.py`) for these actions. These scripts are wrappers that ensure correct Scope handling and Sync logic.
3.  **Interaction First**: If the user gives a generic command like "uninstall skills" or "update tools", **DO NOT** ask for names or run `list_skills` first. Directly launch the corresponding script without arguments to provide the user with a TUI selection menu.
4.  **No Assumptions**: Never decide the `scope` (Global/Project) or the specific `item` to uninstall. Use the interactive mode of the scripts to let the user decide.
5.  **Verification**: Always use `python3 scripts/list_skills.py` to confirm the current state before making suggestions.
