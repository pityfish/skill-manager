#!/usr/bin/env python3
"""
List all skills in central repo and their sync status across all detected platforms.
Shows installation source (npx skills vs Git/Local) and update status.
"""

import json
import subprocess
import concurrent.futures
from pathlib import Path

# Import central configuration
import config


def check_git_remote_status(repo_path: Path) -> tuple[str, str]:
    """
    Check if a git repo has updates available.
    Returns: (status_code, status_message)
    status_code: 'up_to_date', 'update_available', 'diverged', 'error', 'not_git'
    """
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        return "not_git", ""

    try:
        # Fetch remote updates (quietly)
        subprocess.run(
            ["git", "fetch"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            timeout=10,
        )

        # Check raw commits behind using rev-list
        # HEAD..@{u} means commits in upstream but not in HEAD
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..@{u}"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )

        behind_count = int(result.stdout.strip())

        if behind_count > 0:
            return "update_available", f" ⬇️  {behind_count} commits behind"

        # Also check if we are ahead (unpushed changes)
        result_ahead = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )
        ahead_count = int(result_ahead.stdout.strip())

        if ahead_count > 0:
            return "up_to_date", f" ⬆️  {ahead_count} commits ahead"

        return "up_to_date", " ✅ Up to date"

    except subprocess.CalledProcessError:
        # Fallback or strict error
        # Maybe no upstream configured?
        return "error", " ❓ Git Error (No upstream?)"
    except subprocess.TimeoutExpired:
        return "error", " ⏱️  Timeout"
    except Exception:
        return "error", " ❓ Error"


def check_path_status(path: Path, expected_source: Path = None) -> tuple[str, str]:
    """
    Check path status.
    Returns (status_icon, description).
    """
    if not path.exists() and not path.is_symlink():
        return "❌", "Not installed"

    if path.is_symlink():
        target = path.resolve()
        if not target.exists():
            return "⚠️ ", "Broken symlink"

        if expected_source and target == expected_source:
            return "✅", f"Synced"
        else:
            return "🔗", f"Linked → {target}"
    else:
        return "📁", "Local directory (not synced)"


def discover_all_skills(available_platforms: dict) -> set[str]:
    """Discover all skills from repo and all available platforms."""
    skills = set()

    # From central repos (Global + Project)
    skills_with_sources = config.get_all_skills_with_sources()
    skills.update(skills_with_sources.keys())

    # From all available platforms
    for p_id, info in available_platforms.items():
        platform_path = info["path"]
        if platform_path.exists():
            for item in platform_path.iterdir():
                if (item.is_dir() or item.is_symlink()) and not item.name.startswith(
                    "."
                ):
                    skills.add(item.name)

    return skills


def list_all_skills():
    """List all skills with their sync status across all platforms."""
    available_platforms = config.get_available_platforms()
    all_skills = sorted(list(discover_all_skills(available_platforms)))

    if not all_skills:
        print("📭 No skills found.")
        print(f"\nGlobal Repo:  {config.SKILL_REPO_GLOBAL}")
        print(f"Project Repo: {config.SKILL_REPO_PROJECT}")
        return

    # Prepare parallel git verification
    # We only check git status for Git-based skills
    git_check_futures = {}

    print(f"📚 All Skills ({len(all_skills)} total)\n")
    print("=" * 80)

    # Get all skills with their sources
    skills_with_sources = config.get_all_skills_with_sources()

    # Start git checks in background for Git-based skills only
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for skill_name in all_skills:
            skill_info = skills_with_sources.get(skill_name)
            if skill_info:
                repo_path = skill_info["path"]
                source_type = skill_info.get("source_type", config.SOURCE_TYPE_UNKNOWN)

                if (
                    source_type == config.SOURCE_TYPE_GIT
                    or (repo_path / ".git").exists()
                ):
                    git_check_futures[skill_name] = executor.submit(
                        check_git_remote_status, repo_path
                    )

    # Count stats by source type
    in_repo_global = 0
    in_repo_project = 0
    synced_count = 0
    updates_available = 0
    source_type_counts = {
        config.SOURCE_TYPE_NPX: 0,
        config.SOURCE_TYPE_GIT: 0,
        config.SOURCE_TYPE_LOCAL: 0,
        config.SOURCE_TYPE_UNKNOWN: 0,
    }

    for skill_name in all_skills:
        skill_info = skills_with_sources.get(skill_name)

        repo_exists = False
        repo_path = None
        scope = "unknown"
        source_type = config.SOURCE_TYPE_UNKNOWN
        source_info = {}

        if skill_info:
            repo_path = skill_info["path"]
            repo_exists = repo_path.exists()
            scope = skill_info.get("scope", "unknown")
            source_type = skill_info.get("source_type", config.SOURCE_TYPE_UNKNOWN)
            source_info = skill_info.get("source_info", {})

        update_status_str = ""
        source_icon = config.get_source_type_icon(source_type)
        source_label = config.get_source_type_label(source_type)

        if repo_exists:
            if scope == "global":
                in_repo_global += 1
            elif scope == "project":
                in_repo_project += 1

            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1

            # Retrieve git status from future (only for Git-based skills)
            if skill_name in git_check_futures:
                status_code, status_msg = git_check_futures[skill_name].result()
                if status_code == "update_available":
                    updates_available += 1
                update_status_str = status_msg

        # Print skill header with source type and scope
        scope_badge = ""
        if scope == "global":
            scope_badge = " [Global]"
        elif scope == "project":
            scope_badge = " [Project]"

        print(
            f"\n{source_icon} {skill_name} [{source_label}]{scope_badge}{update_status_str}"
        )

        # Show source details for npx skills
        if source_type == config.SOURCE_TYPE_NPX and source_info:
            source_repo = source_info.get("source", "")
            if source_repo:
                print(f"   Source:       {source_repo}")

        # Repo status
        if repo_exists:
            print(f"   Repo:         ✅ {repo_path}")
        else:
            print(f"   Repo:         ❌ Not in any repo (Orphaned in platforms?)")

        expected_source = repo_path if repo_exists else None
        platforms_synced = 0

        for p_id, info in available_platforms.items():
            # Determine path based on scope
            platform_target_root = config.get_platform_target_path(p_id, scope)

            # If scope is unknown or we can't determine target, fallback to info['path'] (global)
            if not platform_target_root:
                platform_target_root = info["path"]

            skill_path = platform_target_root / skill_name
            icon, desc = check_path_status(skill_path, expected_source)

            print(f"   {info['name']:18} {icon} {desc}")

            if icon == "✅":
                platforms_synced += 1

        if platforms_synced > 0:
            synced_count += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Total skills:     {len(all_skills)}")
    print(f"   Global Repo:      {in_repo_global}")
    print(f"   Project Repo:     {in_repo_project}")
    print(f"   Synced to 1+ platforms: {synced_count}")

    # Source type breakdown
    print(f"\n📦 By Installation Source:")
    if source_type_counts[config.SOURCE_TYPE_NPX] > 0:
        print(
            f"   {config.get_source_type_icon(config.SOURCE_TYPE_NPX)} npx skills:  {source_type_counts[config.SOURCE_TYPE_NPX]}"
        )
    if source_type_counts[config.SOURCE_TYPE_GIT] > 0:
        print(
            f"   {config.get_source_type_icon(config.SOURCE_TYPE_GIT)} Git:         {source_type_counts[config.SOURCE_TYPE_GIT]}"
        )
    if source_type_counts[config.SOURCE_TYPE_LOCAL] > 0:
        print(
            f"   {config.get_source_type_icon(config.SOURCE_TYPE_LOCAL)} Local:       {source_type_counts[config.SOURCE_TYPE_LOCAL]}"
        )
    if source_type_counts[config.SOURCE_TYPE_UNKNOWN] > 0:
        print(
            f"   {config.get_source_type_icon(config.SOURCE_TYPE_UNKNOWN)} Unknown:     {source_type_counts[config.SOURCE_TYPE_UNKNOWN]}"
        )

    if updates_available > 0:
        print(f"\n⬇️  Updates available: {updates_available}")
        print(f"   - Git skills: python3 scripts/update_skills.py")
        print(f"   - npx skills: npx skills update")

    # Show paths
    print(f"\n📍 Available Platform Paths:")
    print(f"   Global Repo:   {config.SKILL_REPO_GLOBAL}")
    print(f"   Project Repo:  {config.SKILL_REPO_PROJECT}")
    for p_id, info in available_platforms.items():
        print(f"   {info['name']:15}: {info['path']}")


def main():
    list_all_skills()


if __name__ == "__main__":
    main()
