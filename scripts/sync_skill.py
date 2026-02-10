#!/usr/bin/env python3
"""
Sync an existing skill (Global or Project) to selected platforms.
Strictly manages symlinks, does NOT install or update code.
"""

import sys
import argparse
from pathlib import Path

# Import central configuration
import config
from install_skill import (
    get_platform_paths,
    ask_sync_targets,
    sync_to_platforms,
    update_sync_metadata,
)


def main():
    parser = argparse.ArgumentParser(
        description="Sync an existing skill to platforms (create symlinks)."
    )
    parser.add_argument("skill_name", help="Name of the installed skill")
    parser.add_argument(
        "--scope",
        choices=["global", "project"],
        default=None,
        help="Target scope: Auto-detect (default), 'global', or 'project'",
    )

    args = parser.parse_args()

    skill_name = args.skill_name
    scope = args.scope

    # Auto-detect scope if not provided
    if scope is None:
        # Check if we are in a project context
        is_in_project = (config.PROJECT_ROOT / ".agents").exists() or (
            config.PROJECT_ROOT / ".git"
        ).exists()

        # Check where the skill actually exists
        global_path = config.SKILL_REPO_GLOBAL / skill_name
        project_path = config.SKILL_REPO_PROJECT / skill_name

        if is_in_project and project_path.exists():
            scope = "project"
            print(f"🏠 Found skill '{skill_name}' in Project Repo.")
        elif global_path.exists():
            scope = "global"
            print(f"🌍 Found skill '{skill_name}' in Global Repo.")
        else:
            # Fallback logic if detection fails but context implies something
            if is_in_project:
                print(
                    "🏠 Project context detected, but skill not found in Project Repo."
                )
                if global_path.exists():
                    print("   Using Global skill instead.")
                    scope = "global"
                else:
                    scope = "project"  # Will fail later
            else:
                scope = "global"

    repo_path = config.get_skill_repo(scope)
    skill_path = repo_path / skill_name

    if not skill_path.exists():
        print(f"❌ Skill '{skill_name}' not found in {scope} repo ({repo_path})")
        print(f"   Run 'python3 scripts/install_skill.py ...' to install it first.")
        sys.exit(1)

    print(f"\n🔗 Syncing skill: {skill_name}")
    print(f"   Source: {skill_path}")

    # Determine target platforms
    available_platforms = get_platform_paths(scope)

    # Ask user which platforms to sync
    sync_targets = ask_sync_targets(available_platforms, scope == "project")

    # Sync to platforms
    sync_to_platforms(
        skill_path, skill_name, sync_targets, available_platforms, force=True
    )

    # Update metadata (preserve existing source info if possible, but here we might not have it easily without loading)
    # We can load existing metadata to get source info
    old_metadata = config.load_metadata(scope).get(skill_name, {})
    source_type = old_metadata.get("source_type", "unknown")
    source_url = old_metadata.get("source_url", None)

    update_sync_metadata(
        skill_name,
        sync_targets,
        available_platforms,
        scope=scope,
        source_type=source_type,
        source_url=source_url,
    )

    print(f"\n✅ Sync complete!")


if __name__ == "__main__":
    main()
