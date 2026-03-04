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
    parser.add_argument(
        "--agents",
        nargs="?",
        const="",
        default=None,
        help="Non-interactive: comma-separated agent IDs to sync to, 'all', or empty to skip syncing",
    )

    args = parser.parse_args()

    skill_name = args.skill_name
    scope = args.scope

    # 解析 --agents 参数
    agent_ids = None
    if args.agents is not None:
        agent_ids = [a.strip() for a in args.agents.split(",") if a.strip()]

    # Find the skill using robust search (supports hierarchical paths)
    skill_info = config.find_installed_skill(skill_name, scope=scope)

    if not skill_info:
        msg_scope = f" in {scope} scope" if scope else ""
        print(f"❌ Skill '{skill_name}' not found{msg_scope}.")
        print(f"   Run 'python3 scripts/install_skill.py ...' to install it first.")
        sys.exit(1)

    # Use the detected/confirmed information
    skill_path = skill_info["path"]
    scope = skill_info["scope"]
    # We might want to use the canonical name for metadata updates later
    canonical_name = skill_info.get("canonical_name", skill_name)

    print(f"🏠 Found skill '{skill_name}' in {scope.capitalize()} Repo.")

    print(f"\n🔗 Syncing skill: {skill_name}")
    print(f"   Source: {skill_path}")

    # Determine target platforms
    available_platforms = get_platform_paths(scope)

    # Ask user which platforms to sync (或通过 --agents 非交互指定)
    sync_targets = ask_sync_targets(
        available_platforms, scope == "project", agent_ids=agent_ids
    )

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
