[中文](./README_CN.md)

# Skill Manager (Unified Skill Management Tool)

**Skill Manager** is a powerful AI Agent skill management tool designed to unify skills from different sources and automatically sync them to your locally installed AI assistants (such as Claude Code, Gemini CLI, Cursor, etc.).

It solves the problem of fragmented an skill ecosystem by unifying `npx skills` (skills.sh ecosystem) and Git/Local skills into a central repository at `~/.agents/skills/`, providing a complete set of lifecycle management scripts.

## ✨ Key Features

*   **🛡️ Unified Repository**: All skills are centrally stored in `~/.agents/skills/`, keeping everything organized.
*   **🌍 Multi-Source Support**:
    *   📦 **skills.sh Ecosystem**: Fully compatible with skills installed via `npx skills`.
    *   🔗 **Git Repositories**: Supports installing directly from GitHub or other Git URLs.
    *   📁 **Local Development**: Supports installing local skill directories.
*   **🔄 Automatic Sync**: Intelligently detects installed AI platforms (e.g., Claude, Gemini, Cursor) and syncs skills via symlinks—install once, use everywhere.
*   **🛠️ Full Lifecycle Management**: Python scripts for installing, listing, updating, and uninstalling skills.
*   **🧠 Smart Recognition**: Automatically identifies the installation source of a skill and invokes the correct update/uninstall logic (e.g., `git pull` vs `npx skills update`).

## 🚀 Supported AI Platforms

The tool automatically detects and syncs with the following platforms:

*   Claude Code (`~/.claude/skills`)
*   GitHub Copilot (`~/.copilot/skills`)
*   Google Antigravity (`~/.gemini/antigravity/skills`)
*   Cursor (`~/.cursor/skills`)
*   OpenCode (`~/.config/opencode/skill`)
*   OpenAI Codex (`~/.codex/skills`)
*   Gemini CLI (`~/.gemini/skills`)
*   Windsurf (`~/.codeium/windsurf/skills`)
*   Qwen Code (`~/.qwen/skills`)
*   Qoder (`~/.qoder/skills`)

## 📦 Installation & Setup

Clone this repository to your local environment (recommended location is `~/.agents/skills/`, or any preferred location):

```bash
git clone https://github.com/your-username/skill-manager.git ~/.agents/skills/skill-manager
```

Ensure the scripts are executable:

```bash
chmod +x ~/.agents/skills/skill-manager/scripts/*.py
```

## 📖 Usage Guide

### 1. List Installed Skills

View all skills, their sources, and sync status:

```bash
python3 scripts/list_synced.py
```

**Example Output**:
> 📦 find-skills [npx skills] - ✅ Synced
> 🔗 my-custom-skill [Git] - ⬇️ 2 commits behind

### 2. Install New Skill

Install from a Git URL or local path, with interactive prompts for platform syncing.

```bash
# Install from Git URL (Global)
python3 scripts/install_skill.py https://github.com/user/awesome-skill.git

# Install from local directory
python3 scripts/install_skill.py ./my-local-skill/

# Install to current project (Local Scope)
python3 scripts/install_skill.py ./my-skill/ --local
```

### 3. Update Skills

Automatically detects skill source and updates accordingly.

```bash
# Interactive Update (Recommended)
python3 scripts/update_skills.py

# Update all Git-based skills
python3 scripts/update_skills.py --all

# Update a specific skill
python3 scripts/update_skills.py my-skill
```

### 4. Uninstall Skill

Smart uninstallation that removes the skill from the central repo and all platform symlinks.

```bash
python3 scripts/uninstall_skill.py <skill-name>
```

For skills installed via `npx`, it recommends using `npx skills remove`.

## 📂 Directory Structure

```text
~/.agents/skills/                 ← Central Repository
    ├── skill-manager/            ← This tool
    ├── my-skill/                 ← User installed skill
    ├── find-skills/              ← npx installed skill
    └── ...

~/.claude/skills/                 ← Platform Directory
    └── my-skill -> ~/.agents/skills/my-skill  ← Auto-created symlink
```

## 🤝 Contribution

Issues and Pull Requests are welcome to improve this tool!
