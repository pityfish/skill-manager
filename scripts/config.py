#!/usr/bin/env python3
import os
import json
from pathlib import Path

# Central Skill Repository (unified with npx skills)
# Global: ~/.agents/skills/  (same as npx skills -g)
# Local:  ./.agents/skills/  (same as npx skills without -g)
SKILL_REPO = Path.home() / ".agents" / "skills"
SYNC_METADATA = Path.home() / ".agents" / ".skill_manager_metadata.json"

# npx skills lock file (for detecting skills installed via npx skills)
NPX_SKILLS_LOCK = Path.home() / ".agents" / ".skill-lock.json"

# Legacy repo path (for migration)
LEGACY_SKILL_REPO = Path.home() / ".skill_repo"

# Installation source types
SOURCE_TYPE_NPX = "npx-skills"      # Installed via npx skills
SOURCE_TYPE_GIT = "git"              # Installed via git clone/url
SOURCE_TYPE_LOCAL = "local"          # Installed from local directory
SOURCE_TYPE_UNKNOWN = "unknown"      # Unknown source

# Supported Platforms Configuration
# Format: { "Display Name": { "id": "internal_id", "global": Path, "local": "local_project_path" } }
SUPPORTED_PLATFORMS = {
    "Claude Code": {
        "id": "claude",
        "global": Path.home() / ".claude" / "skills",
        "local": ".claude/skills"
    },
    "GitHub Copilot": {
        "id": "copilot",
        "global": Path.home() / ".copilot" / "skills",
        "local": ".github/skills"
    },
    "Google Antigravity": {
        "id": "antigravity",
        "global": Path.home() / ".gemini" / "antigravity" / "skills",
        "local": ".agent/skills"
    },
    "Cursor": {
        "id": "cursor",
        "global": Path.home() / ".cursor" / "skills",
        "local": ".cursor/skills"
    },
    "OpenCode": {
        "id": "opencode",
        "global": Path.home() / ".config" / "opencode" / "skill",
        "local": ".opencode/skill"
    },
    "OpenAI Codex": {
        "id": "codex",
        "global": Path.home() / ".codex" / "skills",
        "local": ".codex/skills"
    },
    "Gemini CLI": {
        "id": "gemini",
        "global": Path.home() / ".gemini" / "skills",
        "local": ".gemini/skills"
    },
    "Windsurf": {
        "id": "windsurf",
        "global": Path.home() / ".codeium" / "windsurf" / "skills",
        "local": ".windsurf/skills"
    },
    "Qwen Code": {
        "id": "qwen",
        "global": Path.home() / ".qwen" / "skills",
        "local": ".qwen/skills"
    },
    "Qoder": {
        "id": "qoder",
        "global": Path.home() / ".qoder" / "skills",
        "local": ".qoder/skills"
    }
}

def get_available_platforms():
    """
    Scan the system to see which platforms are installed.
    A platform is considered 'available' if its global parent directory exists.
    """
    available = {}
    for name, config in SUPPORTED_PLATFORMS.items():
        # Check if the parent directory of the skills folder exists
        # e.g., for ~/.claude/skills, check if ~/.claude exists
        global_path = config["global"]
        if global_path.parent.exists():
            available[config["id"]] = {
                "name": name,
                "path": global_path,
                "local_path": config["local"]
            }
    return available

def load_metadata():
    """Load sync metadata from file."""
    if SYNC_METADATA.exists():
        with open(SYNC_METADATA, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_metadata(metadata):
    """Save sync metadata to file."""
    SKILL_REPO.mkdir(parents=True, exist_ok=True)
    with open(SYNC_METADATA, 'w') as f:
        json.dump(metadata, f, indent=2)

def load_npx_skills_lock():
    """Load npx skills lock file."""
    if NPX_SKILLS_LOCK.exists():
        with open(NPX_SKILLS_LOCK, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def get_skill_source_type(skill_name: str) -> tuple[str, dict]:
    """
    Determine the installation source of a skill.
    Returns: (source_type, source_info)

    source_type: 'npx-skills', 'git', 'local', or 'unknown'
    source_info: dict with details about the source
    """
    # Check npx skills lock first
    npx_lock = load_npx_skills_lock()
    if "skills" in npx_lock and skill_name in npx_lock["skills"]:
        info = npx_lock["skills"][skill_name]
        return SOURCE_TYPE_NPX, {
            "source": info.get("source", ""),
            "source_url": info.get("sourceUrl", ""),
            "installed_at": info.get("installedAt", ""),
            "updated_at": info.get("updatedAt", ""),
        }

    # Check skill-manager metadata
    metadata = load_metadata()
    if skill_name in metadata:
        info = metadata[skill_name]
        source_type = info.get("source_type", SOURCE_TYPE_UNKNOWN)
        return source_type, info

    # Check if it's a git repo
    skill_path = SKILL_REPO / skill_name
    if skill_path.exists() and (skill_path / ".git").exists():
        return SOURCE_TYPE_GIT, {"source": str(skill_path)}

    # If exists but no metadata, it's unknown/local
    if skill_path.exists():
        return SOURCE_TYPE_LOCAL, {"source": str(skill_path)}

    return SOURCE_TYPE_UNKNOWN, {}

def get_all_skills_with_sources() -> dict:
    """
    Get all skills with their source information.
    Returns: { skill_name: { "source_type": str, "source_info": dict, "path": Path } }
    """
    skills = {}

    # Scan central repo
    if SKILL_REPO.exists():
        for item in SKILL_REPO.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                source_type, source_info = get_skill_source_type(item.name)
                skills[item.name] = {
                    "source_type": source_type,
                    "source_info": source_info,
                    "path": item,
                }

    return skills

def get_source_type_icon(source_type: str) -> str:
    """Get icon for source type."""
    icons = {
        SOURCE_TYPE_NPX: "📦",      # npx skills
        SOURCE_TYPE_GIT: "🔗",       # git
        SOURCE_TYPE_LOCAL: "📁",     # local
        SOURCE_TYPE_UNKNOWN: "❓",   # unknown
    }
    return icons.get(source_type, "❓")

def get_source_type_label(source_type: str) -> str:
    """Get human-readable label for source type."""
    labels = {
        SOURCE_TYPE_NPX: "npx skills",
        SOURCE_TYPE_GIT: "Git",
        SOURCE_TYPE_LOCAL: "Local",
        SOURCE_TYPE_UNKNOWN: "Unknown",
    }
    return labels.get(source_type, "Unknown")
