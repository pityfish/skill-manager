#!/usr/bin/env python3
import os
import json
from pathlib import Path

# Central Skill Repository (unified with npx skills)
# Global: ~/.agents/skills/  (same as npx skills -g)
SKILL_REPO_GLOBAL = Path.home() / ".agents" / "skills"

# Project-Level: ./.agents/skills/ (same as npx skills without -g)
SKILL_REPO_PROJECT = Path.cwd() / ".agents" / "skills"

# Initial Metadata paths
SYNC_METADATA_GLOBAL = Path.home() / ".agents" / ".skill_manager_metadata.json"
SYNC_METADATA_PROJECT = Path.cwd() / ".agents" / ".skill_manager_metadata.json"

# npx skills lock file (for detecting skills installed via npx skills)
NPX_SKILLS_LOCK_GLOBAL = Path.home() / ".agents" / ".skill-lock.json"
NPX_SKILLS_LOCK_PROJECT = Path.cwd() / ".agents" / ".skill-lock.json"

# Legacy repo path (for migration)
LEGACY_SKILL_REPO = Path.home() / ".skill_repo"

# Installation source types
SOURCE_TYPE_NPX = "npx-skills"  # Installed via npx skills
SOURCE_TYPE_GIT = "git"  # Installed via git clone/url
SOURCE_TYPE_LOCAL = "local"  # Installed from local directory
SOURCE_TYPE_UNKNOWN = "unknown"  # Unknown source

# Supported Platforms Configuration
# Format: { "Display Name": { "id": "internal_id", "global": Path, "local": "local_project_path" } }
SUPPORTED_PLATFORMS = {
    "AdaL": {
        "id": "adal",
        "global": Path.home() / ".adal/skills",
        "local": ".adal/skills",
    },
    "Amp": {
        "id": "amp",
        "global": Path.home() / ".config/agents/skills",
        "local": ".agents/skills",
    },
    "Antigravity": {
        "id": "antigravity",
        "global": Path.home() / ".gemini/antigravity/skills",
        "local": ".agent/skills",
    },
    "Augment": {
        "id": "augment",
        "global": Path.home() / ".augment/skills",
        "local": ".augment/skills",
    },
    "Claude Code": {
        "id": "claude-code",
        "global": Path.home() / ".claude/skills",
        "local": ".claude/skills",
    },
    "Cline": {
        "id": "cline",
        "global": Path.home() / ".cline/skills",
        "local": ".cline/skills",
    },
    "CodeBuddy": {
        "id": "codebuddy",
        "global": Path.home() / ".codebuddy/skills",
        "local": ".codebuddy/skills",
    },
    "Codex": {
        "id": "codex",
        "global": Path.home() / ".codex/skills",
        "local": ".agents/skills",
    },
    "Command Code": {
        "id": "command-code",
        "global": Path.home() / ".commandcode/skills",
        "local": ".commandcode/skills",
    },
    "Continue": {
        "id": "continue",
        "global": Path.home() / ".continue/skills",
        "local": ".continue/skills",
    },
    "Crush": {
        "id": "crush",
        "global": Path.home() / ".config/crush/skills",
        "local": ".crush/skills",
    },
    "Cursor": {
        "id": "cursor",
        "global": Path.home() / ".cursor/skills",
        "local": ".cursor/skills",
    },
    "Droid": {
        "id": "droid",
        "global": Path.home() / ".factory/skills",
        "local": ".factory/skills",
    },
    "Gemini CLI": {
        "id": "gemini-cli",
        "global": Path.home() / ".gemini/skills",
        "local": ".agents/skills",
    },
    "GitHub Copilot": {
        "id": "github-copilot",
        "global": Path.home() / ".copilot/skills",
        "local": ".agents/skills",
    },
    "Goose": {
        "id": "goose",
        "global": Path.home() / ".config/goose/skills",
        "local": ".goose/skills",
    },
    "Junie": {
        "id": "junie",
        "global": Path.home() / ".junie/skills",
        "local": ".junie/skills",
    },
    "iFlow CLI": {
        "id": "iflow-cli",
        "global": Path.home() / ".iflow/skills",
        "local": ".iflow/skills",
    },
    "Kilo Code": {
        "id": "kilo",
        "global": Path.home() / ".kilocode/skills",
        "local": ".kilocode/skills",
    },
    "Kimi Code CLI": {
        "id": "kimi-cli",
        "global": Path.home() / ".config/agents/skills",
        "local": ".agents/skills",
    },
    "Kiro CLI": {
        "id": "kiro-cli",
        "global": Path.home() / ".kiro/skills",
        "local": ".kiro/skills",
    },
    "Kode": {
        "id": "kode",
        "global": Path.home() / ".kode/skills",
        "local": ".kode/skills",
    },
    "MCPJam": {
        "id": "mcpjam",
        "global": Path.home() / ".mcpjam/skills",
        "local": ".mcpjam/skills",
    },
    "Mistral Vibe": {
        "id": "mistral-vibe",
        "global": Path.home() / ".vibe/skills",
        "local": ".vibe/skills",
    },
    "Mux": {
        "id": "mux",
        "global": Path.home() / ".mux/skills",
        "local": ".mux/skills",
    },
    "Neovate": {
        "id": "neovate",
        "global": Path.home() / ".neovate/skills",
        "local": ".neovate/skills",
    },
    "OpenClaw": {
        "id": "openclaw",
        "global": Path.home() / ".moltbot/skills",
        "local": "skills",
    },
    "OpenCode": {
        "id": "opencode",
        "global": Path.home() / ".config/opencode/skills",
        "local": ".agents/skills",
    },
    "OpenHands": {
        "id": "openhands",
        "global": Path.home() / ".openhands/skills",
        "local": ".openhands/skills",
    },
    "Pi": {
        "id": "pi",
        "global": Path.home() / ".pi/agent/skills",
        "local": ".pi/skills",
    },
    "Pochi": {
        "id": "pochi",
        "global": Path.home() / ".pochi/skills",
        "local": ".pochi/skills",
    },
    "Qoder": {
        "id": "qoder",
        "global": Path.home() / ".qoder/skills",
        "local": ".qoder/skills",
    },
    "Qwen Code": {
        "id": "qwen-code",
        "global": Path.home() / ".qwen/skills",
        "local": ".qwen/skills",
    },
    "Replit": {
        "id": "replit",
        "global": Path.home() / ".config/agents/skills",
        "local": ".agents/skills",
    },
    "Roo Code": {
        "id": "roo",
        "global": Path.home() / ".roo/skills",
        "local": ".roo/skills",
    },
    "Trae": {
        "id": "trae",
        "global": Path.home() / ".trae/skills",
        "local": ".trae/skills",
    },
    "Trae CN": {
        "id": "trae-cn",
        "global": Path.home() / ".trae-cn/skills",
        "local": ".trae/skills",
    },
    "Windsurf": {
        "id": "windsurf",
        "global": Path.home() / ".codeium/windsurf/skills",
        "local": ".windsurf/skills",
    },
    "Zencoder": {
        "id": "zencoder",
        "global": Path.home() / ".zencoder/skills",
        "local": ".zencoder/skills",
    },
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
                "local_path": config["local"],
            }
    return available


def get_platform_target_path(platform_id: str, scope: str) -> Path:
    """Get the target path for a skill in a platform, given the scope."""
    # Find config for platform
    conf = None
    for name, c in SUPPORTED_PLATFORMS.items():
        if c["id"] == platform_id:
            conf = c
            break

    if not conf:
        return None

    if scope == "project":
        return Path.cwd() / conf["local"]
    else:
        return conf["global"]


def get_skill_repo(scope: str = "global") -> Path:
    """Get skill repo path based on scope."""
    if scope == "project":
        return SKILL_REPO_PROJECT
    return SKILL_REPO_GLOBAL


def get_metadata_path(scope: str = "global") -> Path:
    """Get metadata path based on scope."""
    if scope == "project":
        return SYNC_METADATA_PROJECT
    return SYNC_METADATA_GLOBAL


def load_metadata(scope: str = "global"):
    """Load sync metadata from file."""
    metadata_path = get_metadata_path(scope)
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_metadata(metadata, scope: str = "global"):
    """Save sync metadata to file."""
    metadata_path = get_metadata_path(scope)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)


def load_npx_skills_lock(scope: str = "global"):
    """Load npx skills lock file."""
    lock_path = (
        NPX_SKILLS_LOCK_PROJECT if scope == "project" else NPX_SKILLS_LOCK_GLOBAL
    )
    if lock_path.exists():
        with open(lock_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def get_skill_source_type(skill_name: str, scope: str = "global") -> tuple[str, dict]:
    """
    Determine the installation source of a skill.
    Returns: (source_type, source_info)

    source_type: 'npx-skills', 'git', 'local', or 'unknown'
    source_info: dict with details about the source
    """
    # Check npx skills lock first
    npx_lock = load_npx_skills_lock(scope)
    if "skills" in npx_lock and skill_name in npx_lock["skills"]:
        info = npx_lock["skills"][skill_name]
        return SOURCE_TYPE_NPX, {
            "source": info.get("source", ""),
            "source_url": info.get("sourceUrl", ""),
            "installed_at": info.get("installedAt", ""),
            "updated_at": info.get("updatedAt", ""),
        }

    # Check skill-manager metadata
    metadata = load_metadata(scope)
    if skill_name in metadata:
        info = metadata[skill_name]
        source_type = info.get("source_type", SOURCE_TYPE_UNKNOWN)
        return source_type, info

    # Check if it's a git repo
    repo_path = get_skill_repo(scope)
    skill_path = repo_path / skill_name
    if skill_path.exists() and (skill_path / ".git").exists():
        return SOURCE_TYPE_GIT, {"source": str(skill_path)}

    # If exists but no metadata, it's unknown/local
    if skill_path.exists():
        return SOURCE_TYPE_LOCAL, {"source": str(skill_path)}

    return SOURCE_TYPE_UNKNOWN, {}


def get_all_skills_with_sources() -> dict:
    """
    Get all skills with their source information from both global and project scopes.
    Returns: { skill_name: { "source_type": str, "source_info": dict, "path": Path, "scope": str } }
    """
    skills = {}

    # Scan global repo
    if SKILL_REPO_GLOBAL.exists():
        for item in SKILL_REPO_GLOBAL.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                source_type, source_info = get_skill_source_type(
                    item.name, scope="global"
                )
                skills[item.name] = {
                    "source_type": source_type,
                    "source_info": source_info,
                    "path": item,
                    "scope": "global",
                }

    # Scan project repo
    if SKILL_REPO_PROJECT.exists():
        for item in SKILL_REPO_PROJECT.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # If skill exists in both, project overrides (or we show both? for now let's use list to distinguish)
                # But for a flat dict, let's prefix key if collision?
                # Actually, caller might want to know about duplicates.
                # Let's just add it, potentially overwriting (which implies project takes precedence in this view)
                source_type, source_info = get_skill_source_type(
                    item.name, scope="project"
                )

                # If we want to preserve both, we might need a different structure.
                # But for now, let's just mark it.
                if item.name in skills:
                    skills[item.name]["project_override"] = True
                    skills[item.name]["project_path"] = item
                else:
                    skills[item.name] = {
                        "source_type": source_type,
                        "source_info": source_info,
                        "path": item,
                        "scope": "project",
                    }

    return skills


def get_source_type_icon(source_type: str) -> str:
    """Get icon for source type."""
    icons = {
        SOURCE_TYPE_NPX: "📦",  # npx skills
        SOURCE_TYPE_GIT: "🔗",  # git
        SOURCE_TYPE_LOCAL: "📁",  # local
        SOURCE_TYPE_UNKNOWN: "❓",  # unknown
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
