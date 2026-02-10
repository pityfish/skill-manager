#!/usr/bin/env python3
"""
Uninstall a skill from central repo and/or selected platforms.
- npx skills: uses `npx skills remove` (with project/global flag)
- Git/Local: removes files directly (central repo + all synced symlinks)
- TUI Mode: provides a unified screen to select locations to clean up
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path

# Import central configuration
import config


def remove_path(path: Path) -> bool:
    """Remove file or directory (including symlinks)."""
    if not path.exists() and not path.is_symlink():
        return False

    if path.is_symlink() or path.is_file():
        path.unlink()
        return True
    elif path.is_dir():
        shutil.rmtree(path)
        return True

    return False


def get_skill_locations(skill_name: str) -> dict:
    """Get all locations where skill exists (Global & Project)."""
    locations = {}

    # 1. Global Repo
    global_repo = config.SKILL_REPO_GLOBAL / skill_name
    if global_repo.exists() or global_repo.is_symlink():
        locations["global_repo"] = {
            "name": "Global Repo",
            "path": global_repo,
            "is_symlink": global_repo.is_symlink(),
            "target": global_repo.resolve() if global_repo.is_symlink() else None,
            "scope": "global",
        }

    # 2. Project Repo
    project_repo = config.SKILL_REPO_PROJECT / skill_name
    if project_repo.exists() or project_repo.is_symlink():
        locations["project_repo"] = {
            "name": "Project Repo",
            "path": project_repo,
            "is_symlink": project_repo.is_symlink(),
            "target": project_repo.resolve() if project_repo.is_symlink() else None,
            "scope": "project",
        }

    # 3. Global Platforms
    global_platforms = config.get_available_platforms()
    for p_id, info in global_platforms.items():
        path = info["path"] / skill_name
        if path.exists() or path.is_symlink():
            is_symlink = path.is_symlink()
            locations[f"global_{p_id}"] = {
                "name": f"Global {info['name']}",
                "path": path,
                "is_symlink": is_symlink,
                "target": path.resolve() if is_symlink else None,
                "scope": "global",
                "platform_id": p_id,
            }

    # 4. Project Platforms
    # Check manual project locations based on supported platforms
    for name, conf in config.SUPPORTED_PLATFORMS.items():
        # Check if parent config exists to be considered "available" or if the skill just exists there
        local_path = config.PROJECT_ROOT / conf["local"] / skill_name
        if local_path.exists() or local_path.is_symlink():
            is_symlink = local_path.is_symlink()
            locations[f"project_{conf['id']}"] = {
                "name": f"Project {name}",
                "path": local_path,
                "is_symlink": is_symlink,
                "target": local_path.resolve() if is_symlink else None,
                "scope": "project",
                "platform_id": conf["id"],
            }

    return locations


def get_synced_symlinks(skill_name: str, locations: dict) -> list[str]:
    """Get list of location keys that are symlinks pointing to a repo."""
    synced = []
    repo_paths = []

    if "global_repo" in locations:
        repo_paths.append(locations["global_repo"]["path"].resolve())
    if "project_repo" in locations:
        repo_paths.append(locations["project_repo"]["path"].resolve())

    for key, info in locations.items():
        if "repo" in key:
            continue

        if info["is_symlink"] and info["target"] in repo_paths:
            synced.append(key)

    return synced


def cleanup_metadata(skill_name: str):
    """Clean up metadata for both scopes after uninstallation."""
    for scope in ["global", "project"]:
        metadata = config.load_metadata(scope)
        if skill_name not in metadata:
            continue

        # Check if source (repo) still exists
        repo_path = config.get_skill_repo(scope) / skill_name
        if not repo_path.exists():
            del metadata[skill_name]
            config.save_metadata(metadata, scope)
            # print(f"   ✅ Removed from {scope} metadata")
            continue

        # Check targets
        current_targets = metadata[skill_name].get("targets", [])
        valid_targets = []
        for t in current_targets:
            t_path = Path(t)
            if t_path.exists() or t_path.is_symlink():
                valid_targets.append(t)

        if len(valid_targets) != len(current_targets):
            metadata[skill_name]["targets"] = valid_targets
            config.save_metadata(metadata, scope)
            # print(f"   ✅ Updated {scope} metadata")


def uninstall_skill_selective(
    skill_name: str, selected_keys: list[str], locations: dict
):
    """Uninstall skill from selected locations only."""
    print(f"\n🗑️  Removing '{skill_name}'...\n")

    removed_any = False

    for key in selected_keys:
        if key not in locations:
            continue
        info = locations[key]
        path = info["path"]

        if remove_path(path):
            print(f"   ✅ Removed from {info['name']}: {path}")
            removed_any = True
        else:
            print(f"   ⚠️  Not found in {info['name']}: {path}")

    # Clean up metadata
    cleanup_metadata(skill_name)

    if removed_any:
        print(f"\n✅ Uninstall complete!")
    else:
        print(f"\n⚠️  Nothing was removed.")


def main():
    if len(sys.argv) < 2:
        print("Usage: uninstall_skill.py <skill-name>")
        sys.exit(1)

    skill_name = sys.argv[1]

    # Find where skill exists
    locations = get_skill_locations(skill_name)

    if not locations:
        print(f"❌ Skill '{skill_name}' not found in any location (Global or Project).")
        sys.exit(1)

    # Count synced symlinks
    synced_symlinks = get_synced_symlinks(skill_name, locations)

    # Detect active scopes
    has_global = any(l["scope"] == "global" for l in locations.values())
    has_project = any(l["scope"] == "project" for l in locations.values())

    # Determine default scope based on Context
    # If we are effectively in a project (config.PROJECT_ROOT has .agents or .git), prefer project
    is_in_project = (config.PROJECT_ROOT / ".agents").exists() or (
        config.PROJECT_ROOT / ".git"
    ).exists()

    default_scope = "project" if (is_in_project and has_project) else "global"
    if default_scope == "global" and not has_global and has_project:
        default_scope = "project"

    print(f"\n📦 Skill '{skill_name}' found in:")

    for key, info in locations.items():
        type_str = "symlink" if info["is_symlink"] else "directory"
        synced_mark = " (synced)" if key in synced_symlinks else ""
        scope_icon = "🌍" if info["scope"] == "global" else "🏠"
        print(
            f"   {scope_icon} {info['name']}: {info['path']} [{type_str}]{synced_mark}"
        )

    # Check source type for npx warning
    # We check global first, then project
    source_type_global, _ = config.get_skill_source_type(skill_name, scope="global")
    source_type_project, _ = config.get_skill_source_type(skill_name, scope="project")

    if source_type_global == config.SOURCE_TYPE_NPX:
        print(f"\n⚠️  This skill is installed GLOBALLY via 'npx skills'.")
        print(f"   Recommended: Use 'npx skills remove -g {skill_name}' to uninstall.")

    if source_type_project == config.SOURCE_TYPE_NPX:
        print(f"\n⚠️  This skill is installed LOCALLY via 'npx skills'.")
        print(
            f"   Recommended: Use 'npx skills remove {skill_name}' (in project root) to uninstall."
        )

    # Try to import TUI
    sys.path.append(str(Path(__file__).parent))
    try:
        import tui
    except ImportError:
        tui = None

    if not tui:
        print("\n⚠️  TUI module missing. Please use standard inputs.")
        # Fallback: Select all locations for removal
        keys_to_remove = list(locations.keys())
        print(f"   Selecting ALL locations for removal (fallback).")
    else:
        # Prepare TUI Options
        options = []
        sections = []

        # Group keys by scope
        project_keys = [k for k, v in locations.items() if v["scope"] == "project"]
        global_keys = [k for k, v in locations.items() if v["scope"] == "global"]

        # Determine defaults
        # If default is project, check project items.
        # If default is global, check global items.
        check_project = default_scope == "project"
        check_global = default_scope == "global"

        # Project Section
        if project_keys:
            sections.append({"title": "Project Scope", "start_index": len(options)})
            for key in project_keys:
                info = locations[key]
                options.append(
                    {
                        "id": key,
                        "label": f"{info['name']} ({info['path']})",
                        "checked": check_project,
                    }
                )

        # Global Section
        if global_keys:
            sections.append({"title": "Global Scope", "start_index": len(options)})
            for key in global_keys:
                info = locations[key]
                options.append(
                    {
                        "id": key,
                        "label": f"{info['name']} ({info['path']})",
                        "checked": check_global,
                    }
                )

        menu = tui.MultiSelectMenu(
            "Select locations to uninstall from", options, sections
        )
        print("\033[2m  ↑↓ move, space select, enter confirm\033[0m")

        try:
            keys_to_remove = menu.run()
        except KeyboardInterrupt:
            print("\n❌ Cancelled.")
            sys.exit(0)

    if not keys_to_remove:
        print("❌ No locations selected.")
        sys.exit(0)

    # Confirmation
    print(f"\n⚠️  Will remove {len(keys_to_remove)} item(s).")
    if input("Confirm? [y/N]: ").strip().lower() != "y":
        print("❌ Cancelled.")
        sys.exit(0)

    uninstall_skill_selective(skill_name, keys_to_remove, locations)


if __name__ == "__main__":
    main()
