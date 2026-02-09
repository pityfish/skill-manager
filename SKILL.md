---
name: skill-manager
description: Unified skill management tool. Manages skills from two sources - (1) skills.sh ecosystem via `npx skills` (use /find-skills), and (2) Git/local skills via Python scripts. All skills stored in unified ~/.agents/skills/ directory. Automatically detects installation source and uses appropriate update/uninstall methods.
---

# Skill Manager

Unified skill management for AI agents. Combines two skill ecosystems into one central repository:

1. **Skills CLI** (`npx skills`) - Skills from the open skills.sh ecosystem → Use `/find-skills`
2. **Git/Local Skills** - Git-based and local skills with cross-platform sync → Use scripts below

**Both methods use the same central repository: `~/.agents/skills/`**

## When to Use This Skill

Use this skill when the user:

- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Wants to install a skill from GitHub, Git URL, or local directory
- Asks to list, update, or uninstall installed skills
- Wants to check skill sync status across platforms

## Installation Source Types

Skills are tracked by their installation source, which determines how to update and uninstall them:

| Icon | Source Type | Update Command | Uninstall Command |
|------|-------------|----------------|-------------------|
| 📦 | npx skills | `npx skills update` | `npx skills remove -g <name>` |
| 🔗 | Git | `python3 scripts/update_skills.py` | `python3 scripts/uninstall_skill.py <name>` |
| 📁 | Local | Manual update | `python3 scripts/uninstall_skill.py <name>` |
| ❓ | Unknown | - | `python3 scripts/uninstall_skill.py <name>` |

## Quick Reference

| Action | Skills CLI (skills.sh) | Git/Local Skills |
|--------|------------------------|------------------|
| **Search** | `npx skills find [query]` | N/A |
| **Install (global)** | `npx skills add <pkg> -g -y` | `python3 scripts/install_skill.py <path-or-url>` |
| **Install (local)** | `npx skills add <pkg> -y` | `python3 scripts/install_skill.py <path-or-url> --local` |
| **List** | `npx skills list [-g]` | `python3 scripts/list_synced.py` |
| **Update** | `npx skills update` | `python3 scripts/update_skills.py [--all]` |
| **Uninstall** | `npx skills remove <pkg>` | `python3 scripts/uninstall_skill.py <name>` |

## Scope: Global vs Local

| Scope | Directory | Description |
|-------|-----------|-------------|
| **Global** | `~/.agents/skills/` | Available to all projects (use `-g` flag) |
| **Local** | `./.agents/skills/` | Project-specific skills |

## Decision Guide: Which Method to Use?

| Scenario | Recommended Method |
|----------|-------------------|
| Looking for popular/community skills | Skills CLI (`npx skills find`) or `/find-skills` |
| Installing from skills.sh | Skills CLI (`npx skills add`) |
| Installing from any Git repo | Git/Local Scripts |
| Installing local skill directory | Git/Local Scripts |
| Need cross-platform sync | Git/Local Scripts |
| Managing team/internal skills | Git/Local Scripts |

---

# Part 1: Skills CLI (skills.sh Ecosystem)

**For detailed usage, invoke `/find-skills` skill.**

Quick commands:
```bash
# Search for skills
npx skills find [query]

# Install a skill globally
npx skills add <owner/repo@skill> -g -y

# Install a skill to current project
npx skills add <owner/repo@skill> -y

# List installed skills
npx skills list      # project-level
npx skills list -g   # global

# Update all skills
npx skills update

# Uninstall a skill
npx skills remove -g <skill-name>
```

Browse skills at: https://skills.sh/

---

# Part 2: Git/Local Skills

Cross-platform skill synchronization tool that manages skills in a central repository and syncs to multiple AI platforms via symbolic links. It automatically scans your system to detect which platforms you use.

## Architecture

```
~/.agents/skills/                 ← Central Repository (unified with npx skills)
    ├── my-skill/
    ├── another-skill/
    └── ...

~/.claude/skills/                 ← Symlink → ~/.agents/skills/
~/.gemini/skills/                 ← Symlink → ~/.agents/skills/
~/.cursor/skills/                 ← Symlink → ~/.agents/skills/
...and other platforms

./.agents/skills/                 ← Project-level skills (local scope)
```

**Scope:**
- **Global** (`-g`): `~/.agents/skills/` - Available to all projects
- **Local**: `./.agents/skills/` - Project-specific skills

## Supported Platforms

The tool automatically detects if any of the following platforms are installed:
- Claude Code (`~/.claude/skills`)
- GitHub Copilot (`~/.copilot/skills`)
- Google Antigravity (`~/.gemini/antigravity/skills`)
- Cursor (`~/.cursor/skills`)
- OpenCode (`~/.config/opencode/skill`)
- OpenAI Codex (`~/.codex/skills`)
- Gemini CLI (`~/.gemini/skills`)
- Windsurf (`~/.codeium/windsurf/skills`)
- Qwen Code (`~/.qwen/skills`)
- Qoder (`~/.qoder/skills`)

## Core Scripts

### 1. Install Skill (`install_skill.py`)

Install a skill to central repo and sync to selected platforms.

**Usage**:
```bash
# Global install (default)
python3 scripts/install_skill.py <path-or-url>

# Project-level install
python3 scripts/install_skill.py <path-or-url> --local
```

**Supported inputs**:
- Local skill directory: `./my-skill/`
- Packaged .skill file: `./my-skill.skill`
- **Git Repository URL**: `https://github.com/user/my-skill.git`

**Flags**:
- `--local`: Install skill to the current project's local configuration (`./.agents/skills/`) instead of global.

**Workflow**:
1. Extract skill name from path, filename, or Git URL
2. **Scan system** (or local project) for available AI platforms
3. Check for conflicts in repo and discovered platforms
4. Ask user confirmation if conflicts exist
5. Install to `~/.agents/skills/` (global) or `./.agents/skills/` (local)
6. Ask user which detected platforms to enable (interactive selection)
7. Create symlinks to selected platforms
8. Update sync metadata with source type

**Platform Selection Menu (Dynamic)**:
```
🔗 Detected platforms. Select which to enable this skill:
   1. Claude Code (~/.claude/skills)
   2. Gemini CLI (~/.gemini/skills)
   3. All detected (default)

Enter choice (e.g. '1' or '3'):
```

**Examples**:
```bash
# Install from cloned GitHub repo (global)
git clone https://github.com/user/awesome-skill.git
python3 ~/.agents/skills/skill-manager/scripts/install_skill.py ./awesome-skill/

# Install from Git URL directly
python3 scripts/install_skill.py https://github.com/user/my-skill.git

# Install to current project only
python3 scripts/install_skill.py ./my-skill/ --local
```

### 2. List All Skills (`list_synced.py`)

Display all skills with their **installation source** and sync status across all detected platforms.

**Usage**:
```bash
python3 scripts/list_synced.py
```

**Source Type Icons**:
| Icon | Source Type | Description |
|------|-------------|-------------|
| 📦 | npx skills | Installed via `npx skills add` |
| 🔗 | Git | Installed from Git repository |
| 📁 | Local | Installed from local directory |
| ❓ | Unknown | Unknown installation source |

**Sync Status Icons**:
| Icon | Meaning |
|------|---------|
| ✅ | Synced (symlink points to central repo) |
| 🔗 | Linked (symlink points elsewhere) |
| 📁 | Local directory (not synced) |
| ❌ | Not installed |
| ⚠️ | Broken symlink |

**Example output**:
```
📚 All Skills (3 total)

================================================================================

📦 find-skills [npx skills]
   Source:       vercel-labs/skills
   Repo:         ✅ ~/.agents/skills/find-skills
   Claude Code        ✅ Synced
   Gemini CLI         ✅ Synced
   Antigravity        ✅ Synced

🔗 my-custom-skill [Git] ⬇️  2 commits behind
   Repo:         ✅ ~/.agents/skills/my-custom-skill
   Claude Code        ✅ Synced
   Gemini CLI         ❌ Not installed

📁 local-skill [Local]
   Repo:         ✅ ~/.agents/skills/local-skill
   Claude Code        ❌ Not installed

================================================================================

📊 Summary:
   Total skills:     3
   In central repo:  3
   Synced to 1+ platforms: 2

📦 By Installation Source:
   📦 npx skills:  1
   🔗 Git:         1
   📁 Local:       1

⬇️  Updates available: 1
   - Git skills: python3 scripts/update_skills.py
   - npx skills: npx skills update
```

### 3. Update Skills (`update_skills.py`)

Update skills based on their installation source. Automatically detects source type and uses appropriate method.

**Usage**:
```bash
# Interactive mode (shows all skills grouped by source)
python3 scripts/update_skills.py

# Update specific Git skill
python3 scripts/update_skills.py my-skill

# Update all Git-based skills
python3 scripts/update_skills.py --all

# Update npx skills (runs npx skills update)
python3 scripts/update_skills.py --npx
```

**Features**:
- **Source Detection**: Automatically identifies how each skill was installed
- **Parallel Check**: Rapidly checks git status for Git-based skills concurrently
- **Grouped Display**: Shows skills grouped by source type (npx/Git/Local)
- **Smart Routing**: Uses `git pull` for Git skills, suggests `npx skills update` for npx skills

**Interactive Menu Example**:
```
📦 Select skills to update:

   🔗 Git-based skills (updatable with git pull):
   1. * my-custom-skill         [⬇️  2 new commits]
   2.   another-skill           [✅ Up to date]

   📦 npx skills (use 'npx skills update' to update):
   3.   find-skills             [vercel-labs/skills]

   📁 Local skills (manual update required):
   4.   local-skill             [Local directory]

   A. Update All Git-based skills
   N. Run 'npx skills update' for npx skills

Enter choice (e.g. '1,2', 'A' for git, 'N' for npx):
```

### 4. Uninstall Skill (`uninstall_skill.py`)

Remove a skill using the appropriate method based on installation source.

**Usage**:
```bash
python3 scripts/uninstall_skill.py <skill-name>
```

**Features**:
- **Source Detection**: Shows how the skill was installed
- **Smart Routing**: For npx skills, recommends using `npx skills remove -g`
- **Complete Uninstall**: Removes central repo + all synced symlinks in one step
- **Selective Removal**: Optional per-location removal for non-synced locations

**Workflow**:
1. Detect installation source (npx skills / Git / Local)
2. Show all locations where skill exists (marks synced symlinks)
3. For npx skills: offer to use `npx skills remove -g` (recommended)
4. For Git/Local: offer complete uninstall (repo + all synced platforms)
5. Confirm before deletion
6. Update sync metadata

**Example for npx skill**:
```
📦 Skill 'find-skills' [npx skills]

📍 Found in 3 location(s):
   - Central Repo: ~/.agents/skills/find-skills [directory]
   - Claude Code: ~/.claude/skills/find-skills [symlink] (synced)
   - Gemini CLI: ~/.gemini/skills/find-skills [symlink] (synced)

   Source: vercel-labs/skills

⚠️  This skill was installed via 'npx skills'.
   Recommended: Use 'npx skills remove -g find-skills' to uninstall.

How do you want to proceed?
   1. Use 'npx skills remove -g' (recommended)
   2. Remove files manually
   3. Cancel

Enter choice [1]:
```

**Example for Git/Local skill**:
```
🔗 Skill 'my-custom-skill' [Git]

📍 Found in 3 location(s):
   - Central Repo: ~/.agents/skills/my-custom-skill [directory]
   - Claude Code: ~/.claude/skills/my-custom-skill [symlink] (synced)
   - Gemini CLI: ~/.gemini/skills/my-custom-skill [symlink] (synced)

🗑️  Uninstall options:
   1. Complete uninstall (central repo + 2 synced platforms)
   2. Cancel

Enter choice [1]:
```

When you choose "Complete uninstall", it removes:
- The skill from central repo (`~/.agents/skills/`)
- All synced symlinks from enabled platforms automatically

## Metadata Tracking

Two metadata files track skill installations:

| File | Purpose |
|------|---------|
| `~/.agents/.skill-lock.json` | npx skills installations (managed by Skills CLI) |
| `~/.agents/.skill_manager_metadata.json` | Git/Local skill installations and sync targets |

## Integration with AI Workflows

### When AI generates a new skill

```bash
# AI creates skill at ./new-skill/
python3 ~/.agents/skills/skill-manager/scripts/install_skill.py ./new-skill/
```

### When cloning from GitHub

```bash
git clone https://github.com/user/awesome-skill.git
python3 ~/.agents/skills/skill-manager/scripts/install_skill.py ./awesome-skill/
```

### When installing from .skill file

```bash
python3 ~/.agents/skills/skill-manager/scripts/install_skill.py ~/Downloads/my-skill.skill
```

## Troubleshooting

**Check sync status and installation sources**:
```bash
python3 ~/.agents/skills/skill-manager/scripts/list_synced.py
```

**Update all skills**:
```bash
# Git-based skills
python3 ~/.agents/skills/skill-manager/scripts/update_skills.py --all

# npx skills
npx skills update
```

**Reinstall/resync a skill**:
```bash
# Re-run install from central repo to update symlinks
python3 ~/.agents/skills/skill-manager/scripts/install_skill.py ~/.agents/skills/my-skill
```

**Permissions**:
```bash
# Ensure scripts are executable
chmod +x ~/.agents/skills/skill-manager/scripts/*.py
```

**Missing directories**:
The scripts automatically create platform directories if they don't exist.

## Migration from Legacy ~/.skill_repo

If you have skills in the old `~/.skill_repo/` directory, move them to `~/.agents/skills/`:
```bash
mv ~/.skill_repo/* ~/.agents/skills/
```
