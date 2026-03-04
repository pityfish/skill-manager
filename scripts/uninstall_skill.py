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
import argparse
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


def remove_npx_skill(skill_name: str, scope: str = "project") -> bool:
    """Remove a skill via npx skills remove."""
    cmd = ["npx", "skills", "remove", skill_name, "-y"]
    if scope == "global":
        cmd.append("-g")

    print(f"   ⚙️  Running '{' '.join(cmd)}'...")
    try:
        # For project scope, we should be in PROJECT_ROOT
        cwd = str(config.PROJECT_ROOT) if scope == "project" else None
        subprocess.run(cmd, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ npx skills remove failed: {e}")
        return False
    except FileNotFoundError:
        print("   ❌ npx not found. Cannot remove via Registry.")
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


def cleanup_metadata(skill_name: str, canonical_name: str = None):
    """Clean up metadata for both scopes after uninstallation."""
    target_key = canonical_name or skill_name
    for scope in ["global", "project"]:
        metadata = config.load_metadata(scope)
        if target_key not in metadata:
            continue

        # Check if source (repo) still exists
        repo_path = config.get_skill_repo(scope) / skill_name
        if not repo_path.exists():
            del metadata[target_key]
            config.save_metadata(metadata, scope)
            # print(f"   ✅ Removed {target_key} from {scope} metadata")
            continue

        # Check targets
        current_targets = metadata[target_key].get("targets", [])
        valid_targets = []
        for t in current_targets:
            t_path = Path(t)
            if t_path.exists() or t_path.is_symlink():
                valid_targets.append(t)

        if len(valid_targets) != len(current_targets):
            metadata[target_key]["targets"] = valid_targets
            config.save_metadata(metadata, scope)
            # print(f"   ✅ Updated {target_key} in {scope} metadata")


def ask_skill_to_uninstall(scope: str) -> list[str]:
    """Interactive TUI menu to select a skill to uninstall from a specific scope."""
    # Try to import TUI
    sys.path.append(str(Path(__file__).parent))
    try:
        import tui
    except ImportError:
        return []

    skills_with_sources = config.get_all_skills_with_sources(scope=scope)
    if not skills_with_sources:
        print(f"📭 No skills found in {scope} scope.")
        return []

    options = []
    for key, info in sorted(skills_with_sources.items()):
        name = info.get("original_name", key)
        path = info["path"]
        source_type = info.get("source_type", config.SOURCE_TYPE_UNKNOWN)
        icon = config.get_source_type_icon(source_type)
        label = f"{icon} {name} ({path})"
        options.append({"id": name, "label": label, "checked": False})

    menu = tui.MultiSelectMenu(
        f"Select skills to uninstall from {scope.capitalize()}", options
    )
    try:
        return menu.run()
    except KeyboardInterrupt:
        return []


def uninstall_skill_selective(
    skill_name: str,
    selected_keys: list[str],
    locations: dict,
    canonical_name: str = None,
):
    """Uninstall skill from selected locations only."""
    print(f"\n🗑️  Removing '{skill_name}'...\n")

    # 1. Check if we are removing from a Repo that is managed by NPX
    removed_via_npx = set()

    for key in selected_keys:
        info = locations.get(key)
        if not info or "repo" not in key:
            continue

        scope = info["scope"]
        source_type, _, _ = config.get_skill_source_type(skill_name, scope=scope)

        if source_type == config.SOURCE_TYPE_NPX:
            if scope not in removed_via_npx:
                if remove_npx_skill(skill_name, scope):
                    removed_via_npx.add(scope)
                    print(f"   ✅ Removed {skill_name} from {scope} Registry")

                    print(f"   ✅ Removed {skill_name} from {scope} Registry")

    # 2. Cleanup remaining paths (in case npx didn't remove everything or for non-npx skills)
    removed_any = len(removed_via_npx) > 0

    for key in selected_keys:
        if key.startswith("_"):  # Skip display-only items (like Universal Agents)
            continue

        if key not in locations:
            continue
        info = locations[key]
        path = info["path"]

        if remove_path(path):
            print(f"   ✅ Removed from {info['name']}: {path}")
            removed_any = True
        elif key not in [f"{s}_repo" for s in removed_via_npx]:
            # Only warn if it wasn't already handle by npx remove
            pass

    # Clean up metadata
    cleanup_metadata(skill_name, canonical_name=canonical_name)

    if removed_any:
        print(f"\n✅ Uninstall complete!")
    else:
        print(f"\n⚠️  Nothing was removed.")


def select_locations_to_uninstall(
    skill_name: str, locations: dict, scope: str, select_all: bool = False
) -> list[str]:
    """询问用户要从哪些位置卸载。支持非交互模式。"""
    # 非交互模式：直接返回所有 location keys
    if select_all:
        return list(locations.keys())

    # Import tui here to ensure it's available
    try:
        import tui
    except ImportError:
        # Fallback to all if tui missing
        return list(locations.keys())

    options = []
    # Sort for consistent display
    for key, info in sorted(locations.items()):
        path = info["path"]
        type_str = "Symlink" if info["is_symlink"] else "Repo"
        label = f"{type_str}: {path}"
        options.append(
            {
                "id": key,
                "label": label,
                "checked": True,  # Default to all checked
            }
        )

    # Add Universal Agents warning if Repo is present
    has_repo = "global_repo" in locations or "project_repo" in locations
    if has_repo:
        available = config.get_available_platforms()
        univ_names = [
            info["name"]
            for pid, info in available.items()
            if pid in config.UNIVERSAL_AGENTS
        ]

        if univ_names:
            univ_str = ", ".join(sorted(univ_names))
            if len(univ_str) > 40:
                univ_str = univ_str[:37] + "..."

            options.append(
                {
                    "id": "_universal_display_only",
                    "label": f"Universal Agents ({univ_str}, etc.) [Native support]",
                    "checked": True,
                    "disabled": True,  # Cannot be unchecked independently of Repo removal
                }
            )

    menu = tui.MultiSelectMenu(
        f"Select locations to remove for '{skill_name}' ({scope})", options
    )
    try:
        return menu.run()
    except KeyboardInterrupt:
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Uninstall a skill from central repo and/or platforms."
    )
    parser.add_argument(
        "skill_name",
        nargs="?",
        default=None,
        help="Name of the skill to uninstall (omit for interactive TUI mode)",
    )
    parser.add_argument(
        "--scope",
        choices=["global", "project"],
        default=None,
        help="Target scope (skip TUI scope selection)",
    )
    parser.add_argument(
        "--all-locations",
        action="store_true",
        help="Non-interactive: remove from all detected locations (skip location TUI)",
    )
    parser.add_argument(
        "--platforms",
        "-p",
        help="Only uninstall from these platforms (comma-separated IDs)",
    )

    args = parser.parse_args()

    # Case 1: Interactive mode (未指定 skill name)
    if not args.skill_name:
        # 选择 scope
        if args.scope:
            selected_scope = args.scope
        else:
            selected_scope = config.ask_scope_tui(
                "Which scope do you want to uninstall from?"
            )

        skills_to_remove = ask_skill_to_uninstall(selected_scope)

        if not skills_to_remove:
            print("❌ No skills selected for uninstallation.")
            return

        platforms_to_filter = []
        if args.platforms:
            platforms_to_filter = [
                p.strip() for p in args.platforms.split(",") if p.strip()
            ]

        for name in skills_to_remove:
            print(f"\n--- Processing '{name}' ---")
            locations = get_skill_locations(name)
            # Filter locations to only the selected scope
            scope_locations = {
                k: v for k, v in locations.items() if v["scope"] == selected_scope
            }

            # Find skills info from the scanned list to get canonical name
            all_skills = config.get_all_skills_with_sources(scope=selected_scope)
            canonical_name = None
            if name in all_skills:
                canonical_name = all_skills[name].get("canonical_name")

            # Apply platform filter if specified
            if platforms_to_filter:
                filtered_locations = {}
                for k, v in scope_locations.items():
                    if v.get("platform_id") in platforms_to_filter:
                        filtered_locations[k] = v

                if not filtered_locations:
                    print(
                        f"⚠️  No matching platforms found for '{name}' among: {', '.join(platforms_to_filter)}"
                    )
                    continue
                scope_locations = filtered_locations

            if not scope_locations:
                print(
                    f"⚠️  Unexpected error: Skill '{name}' not found in {selected_scope} scope anymore."
                )
                continue

            # 选择要移除的位置
            keys_to_remove = select_locations_to_uninstall(
                name,
                scope_locations,
                selected_scope,
                select_all=args.all_locations,
            )

            if not keys_to_remove:
                print(f"⏩ Skipping '{name}' (no locations selected).")
                continue

            uninstall_skill_selective(
                name, keys_to_remove, scope_locations, canonical_name=canonical_name
            )
        return

    # Case 2: 指定了 skill name
    skill_name = args.skill_name
    locations = get_skill_locations(skill_name)

    if not locations:
        print(f"❌ Skill '{skill_name}' not found in any location (Global or Project).")
        sys.exit(1)

    # Detect active scopes
    has_global = any(l["scope"] == "global" for l in locations.values())
    has_project = any(l["scope"] == "project" for l in locations.values())

    selected_scope = args.scope
    if selected_scope is None:
        if has_global and has_project:
            selected_scope = config.ask_scope_tui(
                f"Skill '{skill_name}' found in both scopes. Select which one to process:"
            )
        elif has_global:
            selected_scope = "global"
        elif has_project:
            selected_scope = "project"

    # Filter locations to selected scope
    final_locations = {
        k: v for k, v in locations.items() if v["scope"] == selected_scope
    }

    # Apply platform filter if specified
    if args.platforms:
        platforms_to_filter = [
            p.strip() for p in args.platforms.split(",") if p.strip()
        ]
        filtered_locations = {}
        for k, v in final_locations.items():
            if v.get("platform_id") in platforms_to_filter:
                filtered_locations[k] = v

        if not filtered_locations:
            print(
                f"❌ No matching platforms found for '{skill_name}' among: {', '.join(platforms_to_filter)}"
            )
            sys.exit(1)
        final_locations = filtered_locations

    synced_symlinks = get_synced_symlinks(skill_name, final_locations)

    print(f"\n📦 Skill '{skill_name}' ({selected_scope.capitalize()}) found in:")
    for key, info in final_locations.items():
        type_str = "symlink" if info["is_symlink"] else "directory"
        synced_mark = " (synced)" if key in synced_symlinks else ""
        print(f"   {info['name']}: {info['path']} [{type_str}]{synced_mark}")

    # Check source type for NPX logic
    source_type, _, canonical_name = config.get_skill_source_type(
        skill_name, scope=selected_scope
    )
    if source_type == config.SOURCE_TYPE_NPX:
        print(
            f"\nℹ️  This skill is installed via 'npx skills' in {selected_scope} scope."
        )
        print(f"   Uninstalling will automatically trigger 'npx skills remove'.")

    # 选择要移除的位置
    keys_to_remove = select_locations_to_uninstall(
        skill_name,
        final_locations,
        selected_scope,
        select_all=args.all_locations,
    )

    if not keys_to_remove:
        print("❌ No locations selected/Cancelled.")
        return

    uninstall_skill_selective(
        skill_name, keys_to_remove, final_locations, canonical_name=canonical_name
    )


if __name__ == "__main__":
    main()
