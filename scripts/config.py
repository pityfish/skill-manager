#!/usr/bin/env python3
import os
import json
from pathlib import Path


def get_project_root() -> Path:
    """Find the project root by looking for .agents directory or .git directory."""
    # 1. Prefer INIT_CWD if available (set by npx/npm)
    env_cwd = os.environ.get("INIT_CWD")
    if env_cwd:
        current = Path(env_cwd).resolve()
    else:
        current = Path.cwd().resolve()

    # Check parent directories up to root
    for parent in [current] + list(current.parents):
        # If we hit home directory, only count it as a project if it has the marker
        # AND we are actually working inside a sub-item, OR if we really want Global to be distinct.
        # Actually, the simplest fix is: if PROJECT_ROOT == HOME, we effectively don't have a "local project" context.
        if (parent / ".agents").exists() or (parent / ".git").exists():
            # If the discovered project root is HOME, we treat it as Global context only
            if parent == Path.home():
                return (
                    current  # Fallback to current, but we'll handle equivalence later
                )
            return parent
    return current


PROJECT_ROOT = get_project_root()

# Central Skill Repository (unified with npx skills)
# Global: ~/.agents/skills/  (same as npx skills -g)
SKILL_REPO_GLOBAL = Path.home() / ".agents" / "skills"

# Project-Level: PROJECT_ROOT/.agents/skills/ (same as npx skills without -g)
SKILL_REPO_PROJECT = PROJECT_ROOT / ".agents" / "skills"

# Initial Metadata paths
SYNC_METADATA_GLOBAL = Path.home() / ".agents" / ".skill_manager_metadata.json"
SYNC_METADATA_PROJECT = PROJECT_ROOT / ".agents" / ".skill_manager_metadata.json"

# npx skills lock file (for detecting skills installed via npx skills)
NPX_SKILLS_LOCK_GLOBAL = Path.home() / ".agents" / ".skill-lock.json"
NPX_SKILLS_LOCK_PROJECT = PROJECT_ROOT / ".agents" / ".skill-lock.json"


# Installation source types
SOURCE_TYPE_NPX = "npx-skills"  # Installed via npx skills
SOURCE_TYPE_GIT = "git"  # Installed via git clone/url
SOURCE_TYPE_LOCAL = "local"  # Installed from local directory
SOURCE_TYPE_UNKNOWN = "unknown"  # Unknown source

# Supported Platforms Configuration
# Format: { "Display Name": { "id": "internal_id", "global": Path, "local": "local_project_path" } }

# Agents that natively support the central skill repo (~/.agents/skills)
# These do NOT need symlinks.
UNIVERSAL_AGENTS = {
    "amp",
    "codex",
    "gemini-cli",
    "github-copilot",
    "kimi-cli",
    "opencode",
}

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
        "global": Path.home() / ".agents/skills",
        "local": ".agents/skills",
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
        "local": ".agents/skills",
    },
    "Droid": {
        "id": "droid",
        "global": Path.home() / ".factory/skills",
        "local": ".factory/skills",
    },
    "Cortex Code": {
        "id": "cortex",
        "global": Path.home() / ".snowflake/cortex/skills",
        "local": ".cortex/skills",
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
        "global": Path.home() / ".openclaw/skills",
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
        return PROJECT_ROOT / conf["local"]
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


def find_installed_skill(name: str, scope: str = None) -> dict:
    """
    Find an installed skill by name (short name or canonical name).
    Returns: { "path": Path, "scope": str, "metadata": dict, "canonical_name": str } or None
    """
    # Use robust searching to find the skill across scopes
    all_skills = get_all_skills_with_sources(scope=scope)

    # 1. Try exact match on key (could be short name or canonical name)
    if name in all_skills:
        return all_skills[name]

    # 2. Try match on canonical_name
    for k, info in all_skills.items():
        if info.get("canonical_name") == name:
            return info

    # 3. Try match on suffix (e.g., 'pptx' matches 'anthropics/skills@pptx')
    for k, info in all_skills.items():
        c_name = info.get("canonical_name")
        if c_name and (c_name.endswith(f"@{name}") or c_name.endswith(f"/{name}")):
            return info

    return None


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


def get_skill_source_type(
    skill_name: str, scope: str = "global"
) -> tuple[str, dict, str]:
    """
    Determine the installation source of a skill.
    Returns: (source_type, source_info, canonical_name)

    source_type: 'npx-skills', 'git', 'local', or 'unknown'
    source_info: dict with details about the source
    canonical_name: the full key used in metadata (e.g. org/repo@skill)
    """
    # Check npx skills lock
    npx_lock = load_npx_skills_lock(scope)
    skills_in_lock = npx_lock.get("skills", {})

    # Check skill-manager metadata
    metadata = load_metadata(scope)

    # 1. Direct match in NPX lock
    if skill_name in skills_in_lock:
        info = skills_in_lock[skill_name]
        return (
            SOURCE_TYPE_NPX,
            {
                "source": info.get("source", ""),
                "source_url": info.get("sourceUrl", ""),
                "installed_at": info.get("installedAt", ""),
                "updated_at": info.get("updatedAt", ""),
            },
            skill_name,
        )

    # 2. Direct match in skill-manager metadata
    if skill_name in metadata:
        info = metadata[skill_name]
        source_type = info.get("source_type", SOURCE_TYPE_UNKNOWN)
        return source_type, info, skill_name

    # 3. Suffix match in NPX lock (for names like org/repo@skill_name)
    for full_id, info in skills_in_lock.items():
        if "@" in full_id and full_id.split("@")[-1] == skill_name:
            return (
                SOURCE_TYPE_NPX,
                {
                    "source": info.get("source", ""),
                    "source_url": info.get("sourceUrl", ""),
                    "installed_at": info.get("installedAt", ""),
                    "updated_at": info.get("updatedAt", ""),
                },
                full_id,
            )

    # 4. Suffix match in skill-manager metadata
    for full_id, info in metadata.items():
        if "@" in full_id and (
            full_id.split("@")[-1] == skill_name
            or ("/" in full_id and full_id.split("/")[-1] == skill_name)
        ):
            source_type = info.get("source_type", SOURCE_TYPE_UNKNOWN)
            return source_type, info, full_id

    # Check physical presence as fallback
    repo_path = get_skill_repo(scope)
    skill_path = repo_path / skill_name

    # Check if it's a git repo
    if skill_path.exists() and (skill_path / ".git").exists():
        return SOURCE_TYPE_GIT, {"source": str(skill_path)}, skill_name

    # If exists but no metadata, it's unknown/local
    if skill_path.exists():
        return SOURCE_TYPE_LOCAL, {"source": str(skill_path)}, skill_name

    return SOURCE_TYPE_UNKNOWN, {}, skill_name


def ask_scope_tui(title: str = "Select scope") -> str:
    """Prompt user to select scope (Global or Project) using TUI."""
    import sys
    from pathlib import Path

    # Optimization: If we are in the HOME directory and no project context was found,
    # default to Global scope immediately without asking.
    if PROJECT_ROOT.resolve() == Path.home().resolve():
        return "global"

    try:
        import tui
    except ImportError:
        sys.path.append(str(Path(__file__).parent))
        try:
            import tui
        except ImportError:
            return "project"

    options = [
        {
            "id": "project",
            "label": "Project (Current directory)",
            "checked": True,
        },
        {"id": "global", "label": "Global (System-wide)", "checked": False},
    ]

    menu = tui.MultiSelectMenu(title, options, single_select=True)
    try:
        selection = menu.run()
        return selection if selection else "project"
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
        sys.exit(0)


def get_all_skills_with_sources(scope: str = None) -> dict:
    """
    Get all skills with their source information.
    If scope is provided, only return skills from that scope.
    Returns: { skill_name: { "source_type": str, "source_info": dict, "path": Path, "scope": str, "canonical_name": str } }
    """
    skills = {}

    scopes_to_check = [scope] if scope else ["global", "project"]

    for s in scopes_to_check:
        repo_path = get_skill_repo(s)
        if not repo_path.exists():
            continue

        # 1. Scan physical directories (Top level)
        for item in repo_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                source_type, source_info, canonical_name = get_skill_source_type(
                    item.name, scope=s
                )

                # Use unique key if collision
                key = item.name
                if key in skills and skills[key]["scope"] != s:
                    key = f"{item.name} ({s})"

                skills[key] = {
                    "source_type": source_type,
                    "source_info": source_info,
                    "canonical_name": canonical_name,
                    "path": item,
                    "scope": s,
                    "original_name": item.name,
                }

        # 2. Integrate hierarchal skills from metadata
        metadata = load_metadata(s)
        for canonical_name, info in metadata.items():
            source_path_str = info.get("source")
            if not source_path_str:
                continue

            source_path = Path(source_path_str)

            # Check if it was already found in top-level scan
            already_in = False
            for k, existing in skills.items():
                if (
                    existing.get("canonical_name") == canonical_name
                    and existing.get("scope") == s
                ):
                    already_in = True
                    break

            if already_in:
                continue

            # Only add if it actually exists (avoid orphans)
            if source_path.exists() or source_path.is_symlink():
                # Use the short name (after @ or /) if possible for the key,
                # but ensure uniqueness
                short_name = canonical_name.split("@")[-1].split("/")[-1]
                key = short_name

                # Handle collision
                if key in skills:
                    if skills[key]["scope"] != s:
                        key = f"{short_name} ({s})"
                    else:
                        key = canonical_name  # Use full name if name collision within same scope

                skills[key] = {
                    "source_type": info.get("source_type", SOURCE_TYPE_UNKNOWN),
                    "source_info": {
                        "source_url": info.get("source_url"),
                        "source_subdir": info.get("source_subdir"),
                        "commit_hash": info.get("commit_hash"),
                    },
                    "canonical_name": canonical_name,
                    "path": source_path,
                    "scope": s,
                    "original_name": short_name,
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
