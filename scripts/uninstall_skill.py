#!/usr/bin/env python3
"""
Uninstall a skill from central repo and/or selected platforms.
Detects installation source and uses appropriate uninstall method:
- npx skills: uses `npx skills remove -g`
- Git/Local: removes files directly (central repo + all synced symlinks)
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


def get_skill_locations(skill_name: str, available_platforms: dict) -> dict:
    """Get all locations where skill exists."""
    locations = {}

    # Check Global Repo
    global_repo = config.SKILL_REPO_GLOBAL / skill_name
    if global_repo.exists() or global_repo.is_symlink():
        locations["global_repo"] = {
            "name": "Global Repo",
            "path": global_repo,
            "is_symlink": global_repo.is_symlink(),
            "target": global_repo.resolve() if global_repo.is_symlink() else None,
            "scope": "global",
        }

    # Check Project Repo
    project_repo = config.SKILL_REPO_PROJECT / skill_name
    if project_repo.exists() or project_repo.is_symlink():
        locations["project_repo"] = {
            "name": "Project Repo",
            "path": project_repo,
            "is_symlink": project_repo.is_symlink(),
            "target": project_repo.resolve() if project_repo.is_symlink() else None,
            "scope": "project",
        }

    # Check all available platforms
    for p_id, info in available_platforms.items():
        path = info["path"] / skill_name
        if path.exists() or path.is_symlink():
            is_symlink = path.is_symlink()
            locations[p_id] = {
                "name": info["name"],
                "path": path,
                "is_symlink": is_symlink,
                "target": path.resolve() if is_symlink else None,
            }

    return locations


def get_synced_symlinks(skill_name: str, locations: dict) -> list[str]:
    """Get list of platform IDs that are symlinks pointing to a repo."""
    synced = []
    repo_paths = []

    if "global_repo" in locations:
        repo_paths.append(locations["global_repo"]["path"].resolve())
    if "project_repo" in locations:
        repo_paths.append(locations["project_repo"]["path"].resolve())

    for p_id, info in locations.items():
        if "repo" in p_id:
            continue

        if info["is_symlink"] and info["target"] in repo_paths:
            synced.append(p_id)

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
            print(f"   ✅ Removed from {scope} metadata")
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
            print(f"   ✅ Updated {scope} metadata")


def uninstall_npx_skill(skill_name: str) -> bool:
    """Uninstall a skill using npx skills remove -g (global)."""
    try:
        print(f"\n📦 Running 'npx skills remove -g {skill_name} -y'...\n")
        subprocess.run(
            ["npx", "skills", "remove", "-g", skill_name, "-y"],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ npx skills remove failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ npx not found. Please install Node.js first.")
        return False


def uninstall_skill_complete(skill_name: str, locations: dict):
    """
    Uninstall skill completely - remove from central repo and all synced platforms.
    """
    print(f"\n🗑️  Removing '{skill_name}' completely...\n")

    removed_count = 0

    # First remove all synced symlinks and platforms
    for p_id, info in locations.items():
        if "repo" in p_id:
            continue  # Handle repos last

        path = info["path"]
        if remove_path(path):
            print(f"   ✅ Removed from {info['name']}: {path}")
            removed_count += 1

    # Then remove from repos
    for repo_key in ["global_repo", "project_repo"]:
        if repo_key in locations:
            repo_info = locations[repo_key]
            if remove_path(repo_info["path"]):
                print(f"   ✅ Removed from {repo_info['name']}: {repo_info['path']}")
                removed_count += 1

    # Clean up metadata
    cleanup_metadata(skill_name)

    if removed_count > 0:
        print(f"\n✅ Uninstall complete! Removed from {removed_count} location(s).")
    else:
        print(f"\n⚠️  Nothing was removed.")


def uninstall_skill_selective(
    skill_name: str, selected_ids: list[str], locations: dict
):
    """Uninstall skill from selected locations only."""
    print(f"\n🗑️  Removing '{skill_name}'...\n")

    removed_any = False

    for p_id in selected_ids:
        if p_id not in locations:
            continue
        info = locations[p_id]
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

    # Get skill source type (check both scopes)
    source_type, source_info = config.get_skill_source_type(skill_name, scope="global")
    if source_type == config.SOURCE_TYPE_UNKNOWN:
        source_type, source_info = config.get_skill_source_type(
            skill_name, scope="project"
        )

    source_icon = config.get_source_type_icon(source_type)
    source_label = config.get_source_type_label(source_type)

    # Get available platforms (to check for skill existence)
    available_platforms = config.get_available_platforms()

    # Find where skill exists
    locations = get_skill_locations(skill_name, available_platforms)

    if not locations:
        print(f"❌ Skill '{skill_name}' not found in any location.")
        sys.exit(1)

    # Count synced symlinks
    synced_symlinks = get_synced_symlinks(skill_name, locations)

    print(f"\n{source_icon} Skill '{skill_name}' [{source_label}]")
    print(f"\n📍 Found in {len(locations)} location(s):")
    for p_id, info in locations.items():
        type_str = "symlink" if info["is_symlink"] else "directory"
        target_info = f" → {info['target']}" if info["is_symlink"] else ""
        synced_mark = " (synced)" if p_id in synced_symlinks else ""
        print(
            f"   - {info['name']}: {info['path']} [{type_str}{target_info}]{synced_mark}"
        )

    # Show source info for npx skills
    if source_type == config.SOURCE_TYPE_NPX and source_info:
        source_repo = source_info.get("source", "")
        if source_repo:
            print(f"\n   Source: {source_repo}")

    # Handle npx skills differently
    if source_type == config.SOURCE_TYPE_NPX:
        print(f"\n⚠️  This skill was installed via 'npx skills'.")
        print(f"   Recommended: Use 'npx skills remove -g {skill_name}' to uninstall.")

        choice = input(
            "\nHow do you want to proceed?\n"
            "   1. Use 'npx skills remove -g' (recommended)\n"
            "   2. Remove files manually\n"
            "   3. Cancel\n"
            "\nEnter choice [1]: "
        ).strip()

        if not choice or choice == "1":
            if uninstall_npx_skill(skill_name):
                print(f"\n✅ Skill '{skill_name}' uninstalled via npx skills.")
            sys.exit(0)
        elif choice == "3":
            print("\n❌ Uninstall cancelled.")
            sys.exit(0)
        # choice == "2" falls through to manual removal

    # For Git/Local skills, show simplified options
    repo_count = 0
    if "global_repo" in locations:
        repo_count += 1
    if "project_repo" in locations:
        repo_count += 1

    print("\n🗑️  Uninstall options:")
    print(
        f"   1. Complete uninstall ({repo_count} repos + {len(synced_symlinks)} synced platforms)"
    )

    # Only show selective option if there are non-synced locations or multiple repos
    non_synced = [
        p_id
        for p_id in locations.keys()
        if "repo" not in p_id and p_id not in synced_symlinks
    ]

    # Always allow selective if we have locations
    print(f"   2. Selective removal (choose specific locations)")
    print(f"   3. Cancel")

    choice = input(f"\nEnter choice [1]: ").strip()

    if not choice or choice == "1":
        # Confirm complete uninstall
        print(f"\n⚠️  This will remove the skill from:")
        if "global_repo" in locations:
            print(f"   - Global Repo ({locations['global_repo']['path']})")
        if "project_repo" in locations:
            print(f"   - Project Repo ({locations['project_repo']['path']})")

        for p_id in synced_symlinks:
            print(f"   - {locations[p_id]['name']} ({locations[p_id]['path']})")

        response = input("\nConfirm complete uninstall? [y/N]: ").strip().lower()
        if response != "y":
            print("❌ Uninstall cancelled.")
            sys.exit(0)

        uninstall_skill_complete(skill_name, locations)

    elif choice == "2":
        # Selective removal
        print("\n🗑️  Select locations to remove:")
        p_ids = list(locations.keys())
        for i, p_id in enumerate(p_ids, 1):
            info = locations[p_id]
            type_str = "symlink" if info["is_symlink"] else "directory"
            print(f"   {i}. {info['name']} [{type_str}]")

        choice = input(f"\nEnter choice (e.g. '1,2'): ").strip()
        if not choice:
            print("\n❌ No locations selected. Uninstall cancelled.")
            sys.exit(0)

        selected_ids = []
        for i, p_id in enumerate(p_ids, 1):
            if str(i) in choice.split(","):
                selected_ids.append(p_id)

        if not selected_ids:
            print("\n❌ No valid locations selected. Uninstall cancelled.")
            sys.exit(0)

        # Confirm
        print(
            f"\n⚠️  Will remove from: {', '.join([locations[pid]['name'] for pid in selected_ids])}"
        )
        response = input("Confirm? [y/N]: ").strip().lower()

        if response != "y":
            print("❌ Uninstall cancelled.")
            sys.exit(0)

        uninstall_skill_selective(skill_name, selected_ids, locations)

    else:
        print("❌ Uninstall cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
