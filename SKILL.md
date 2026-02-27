---
name: skill-manager
description: Unified Agent Capability Manager. Use this skill to: 1) AUDIT and LIST your installed tools/capabilities. 2) FIND and INSTALL new skills (npx/Git/Local) to expand your toolset. 3) SYNC, UPDATE, or UNINSTALL existing skills across Global/Project scopes. Always use this first for self-correction or when you lack a required tool.
---

# Agent Skill Manager (ASM)

This is your **primary hub** for managing, auditing, and expanding your own functional capabilities. Whenever you or the user needs to know what tools are installed or want to add/remove a "skill", use this tool.

> **IMPORTANT**: All scripts support **non-interactive (CLI argument) mode**. You **MUST** always use CLI arguments (`--scope`, `--agents`, `--yes`, etc.) to avoid TUI prompts, since not all agents can display interactive menus.

## 🛠️ Capabilities

### 1. 🔍 Find Skills
**Usage**: Discover capabilities you don't have.
**Constraint**: **ONLY** list results. Do **NOT** install anything unless explicitly ordered by the user.
```bash
npx skills find <search_query>
```

### 2. ⬇️ Install Skill
**Usage**: Install a skill explicitly requested by the user from any source (Registry name, Git URL, or Local Path).
**Constraint**: You **MUST** use the following script. **NEVER** use `npx skills add` directly.

```bash
python3 <path_to_skill_manager>/scripts/install_skill.py <skill_source> --scope <global|project> --agents all --yes
```
| Argument | Required | Description |
|----------|----------|-------------|
| `<skill_source>` | Yes | Git URL, local path, or registry name |
| `--scope <global\|project>` | Yes | Installation scope. Ask user if unclear. |
| `--agents <ids\|all>` | Yes | Comma-separated agent IDs or `all` |
| `--yes` | Recommended | Auto-confirm overwrites |
| `--skills <names\|all>` | For multi-skill repos | Comma-separated skill subdirectory names or `all` |

### 3. 📋 List & Check Skills
**Usage**: List all installed skills, check current capabilities, and verify sync status.
```bash
python3 <path_to_skill_manager>/scripts/list_skills.py
```

### 4. 🔄 Sync Skill
**Usage**: Fix missing tools or sync to a new agent environment.
```bash
python3 <path_to_skill_manager>/scripts/sync_skill.py <skill_name> --scope <global|project> --agents all
```
| Argument | Required | Description |
|----------|----------|-------------|
| `<skill_name>` | Yes | Name of the installed skill |
| `--scope <global\|project>` | Optional | Scope (auto-detected if omitted) |
| `--agents <ids\|all>` | Yes | Comma-separated agent IDs or `all` |

### 5. 🆙 Update Skills
**Usage**: Update installed skills to latest versions.
```bash
python3 <path_to_skill_manager>/scripts/update_skills.py --all --scope <global|project>
```
| Argument | Required | Description |
|----------|----------|-------------|
| `--all` | Yes | Update all Git-based skills without prompting |
| `--scope <global\|project>` | Yes | Target scope |
| `--npx` | Optional | Also run `npx skills update` |
| `<skill_names...>` | Alternative to `--all` | Specific skill names to update |

### 6. 🗑️ Uninstall Skill
**Usage**: Remove a skill and clean up configurations.
```bash
python3 <path_to_skill_manager>/scripts/uninstall_skill.py <skill_name> --scope <global|project> --all-locations
```
| Argument | Required | Description |
|----------|----------|-------------|
| `<skill_name>` | Yes | Name of the skill to uninstall |
| `--scope <global\|project>` | Yes | Target scope. Ask user if unclear. |
| `--all-locations` | Recommended | Remove from all detected locations |

## 🧠 Agent Protocol

1.  **Non-Interactive Mode Only**: You **MUST** always use CLI arguments to run scripts non-interactively. **NEVER** run scripts without arguments expecting TUI menus. Extract required parameters (`scope`, `skill_name`, etc.) from the user's message. If a required parameter **cannot be determined**, ask the user for clarification before executing.
2.  **Strictly Non-Autonomous Installation**: After running `npx skills find`, you must show the list to the user and wait. **Proactive installation is strictly forbidden.**
3.  **No Direct NPX Calls**: You **MUST NOT** call `npx skills add` or `npx skills remove` directly. Use the provided Python scripts (`install_skill.py`, `uninstall_skill.py`) for these actions.
4.  **Parameter Extraction**: When the user says "install X globally", extract `scope=global`. When the user says "uninstall Y", extract `skill_name=Y` and ask for scope if ambiguous.
5.  **Default Sync Strategy**: Always use `--agents all` to sync to all detected platforms unless the user specifies otherwise.
6.  **Verification**: Always use `python3 <path_to_skill_manager>/scripts/list_skills.py` to confirm the current state before making suggestions.
7.  **Context Awareness**: You **MUST** execute these scripts from the **User's Current Working Directory (Project Root)**. Do **NOT** `cd` into the `scripts/` folder or the `skill-manager` repository.
8.  **Path Resolution**: The `skill-manager` might be installed Globally (`~/.agents/skills/skill-manager`) or Locally in the project (`.agents/skills/skill-manager`). You must **detect** where it is installed and execute the scripts using that path. Do not assume it is always global.
    *   Example (Global): `python3 ~/.agents/skills/skill-manager/scripts/install_skill.py`
    *   Example (Project): `python3 .agents/skills/skill-manager/scripts/install_skill.py`
9.  **GitHub Pre-Check Protocol**: When installing from a GitHub URL, `install_skill.py` will automatically analyze the repo structure after cloning:
    *   **Root `SKILL.md` found**: Proceeds with normal installation (pure skill repo).
    *   **Sub-directory `SKILL.md`(s) found**: Use `--skills all` or `--skills name1,name2` to select. Review the output and assist the user.
    *   **No `SKILL.md` found**: The script will print the repo's **README** content. You **MUST carefully read** this output, understand the repo's installation instructions, and then guide the user accordingly. Use `--yes` to force-install only if the user explicitly confirms.

