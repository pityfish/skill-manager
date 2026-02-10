---
name: skill-manager
description: The Skill Manager for AI Agents. Use this to find, install, sync, and manage skills for yourself and other agents.
---

# Agent Skill Manager (ASM)

This is your **primary tool** for managing your own capabilities. Use this to install new tools, sync them across environments, and keep them updated.

## 🛠️ Capabilities

### 1. 🔍 Find Knowledge/Tools
**Usage**: When you need a capability you don't have (e.g., "I need to search the web", "I need to read PDF files").
**Command**:
```bash
npx skills find <search_query>
```

### 2. ⬇️ Install Skill
**Usage**: When you identify a package or Git repo to install.

**Decision Logic (Scope)**:
- **Global**: For general-purpose tools (e.g., `browser`, `clipboard`, `shell`) that should be available in **ALL** your workspaces. Select this in the TUI when prompted.
- **Project**: For workspace-specific tools (e.g., `linter`, `test-runner`) that are only relevant to the current project.

**Commands**:
```bash
# Option A: From Community Registry (Preferred)
npx skills add <package_name> -g -y  # Global Install
npx skills add <package_name> -y     # Project Install

# Option B: From Git URL (Custom/Private)
python3 scripts/install_skill.py <git_url> --scope global
python3 scripts/install_skill.py <git_url> --scope project
```

### 3. 📋 List & Check Status
**Usage**: View all installed skills and check if they are properly synced to your current environment.
**Command**:
```bash
python3 scripts/list_skills.py
```
*Tip: Pay attention to the `Sync Status` column.*

### 4. 🔄 Sync/Fix Skill
**Usage**:
1. If installed skills are **missing** from your tool list.
2. To register an existing skill with a newly added agent.
**Command**:
```bash
python3 scripts/sync_skill.py <skill_name>
```

### 5. 🆙 Update All Skills
**Usage**: Update all installed skills to their latest versions.
**Command**:
```bash
# Interactive Mode
python3 scripts/update_skills.py

# Automated Mode (Recommended for Agents)
python3 scripts/update_skills.py --all --npx
```

### 6. 🗑️ Uninstall Skill
**Usage**: Remove a skill and clean up its configuration.
**Command**:
```bash
python3 scripts/uninstall_skill.py <skill_name>
```

## 🧠 Agent Protocol

1.  **Search First**: Do not assume tools exist. Use `npx skills find` to discover availability.
2.  **Verify Scope**: Always determine if a tool is "Global" (meant for you, the agent) or "Project" (meant for the repo).
3.  **Self-Correction**:
    -   If you install a tool but cannot see it: **DO NOT install again**.
    -   Run `python3 scripts/list_skills.py` to verify it exists.
    -   Run `python3 scripts/sync_skill.py <name>` to force a config sync.
