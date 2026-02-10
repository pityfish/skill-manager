---
name: skill-manager
description: The Skill Manager for AI Agents. Use this to find, install, sync, and manage skills.
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
- **Global**: For general-purpose tools (e.g., `browser`, `clipboard`, `shell`) that should be available in **ALL** your workspaces.
- **Project**: For workspace-specific tools (e.g., `linter`, `test-runner`) that are only relevant to the current project.

**Interactive Flow**: The script will **always** prompt you to select the scope via TUI unless specified.

**Commands**:
```bash
# Option A: From Community Registry (Preferred)
npx skills add <package_name> -g -y  # Global Install
npx skills add <package_name> -y     # Project Install

# Option B: From Git URL (Custom/Private)
python3 scripts/install_skill.py <git_url>
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

### 5. 🆙 Update Skills
**Usage**: Update installed skills to their latest versions.
**Interactive Flow**: Select Scope (Global/Project) -> Select Skills to update.
**Command**:
```bash
# Interactive Mode (Recommended)
python3 scripts/update_skills.py

# Smart Update Single Skill (Auto-detects Git vs Registry)
python3 scripts/update_skills.py <skill_name>

# Automated Update All (Recommended for periodic maintenance)
python3 scripts/update_skills.py --all --npx
```

### 6. 🗑️ Uninstall Skill
**Usage**: Remove a skill and clean up its configuration.
**Interactive Flow**:
- **Option A (TUI Guided)**: Run without arguments to select Scope -> select Skills.
- **Option B (Direct)**: Provide skill name; it will ask for scope if it exists in both.
**Command**:
```bash
python3 scripts/uninstall_skill.py [skill_name]
```
*Note: This automatically triggers `npx skills remove` for Registry skills.*
