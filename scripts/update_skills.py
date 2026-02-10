#!/usr/bin/env python3
"""
Update skills in the central repository.
Detects installation source and uses appropriate update method:
- npx skills: uses `npx skills update`
- Git: uses `git pull`
- Local: shows warning (manual update required)
"""

import os
import sys
import argparse
import subprocess
import concurrent.futures
from pathlib import Path

# Import central configuration
import config


def get_git_repo_status(repo_path: Path) -> str:
    """Check if a directory is a git repo."""
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        return "not_git"
    return "git"


def check_updates_available(repo_path: Path) -> tuple[bool, str]:
    """
    Check if updates are available for a git repo.
    Returns (has_updates, detail_string)
    """
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
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..@{u}"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )

        behind_count = int(result.stdout.strip())

        if behind_count > 0:
            return True, f"⬇️  {behind_count} new commits"

        # Check if ahead
        result_ahead = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )
        ahead_count = int(result_ahead.stdout.strip())

        if ahead_count > 0:
            return False, f"⬆️  {ahead_count} commits ahead"

        return False, "✅ Up to date"

    except (subprocess.CalledProcessError, ValueError):
        # If no upstream, or not a repo
        return False, "❓ Git Error (No upstream?)"
    except subprocess.TimeoutExpired:
        return False, "⏱️  Timeout"


def update_git_repo(repo_path: Path) -> str:
    """Run git pull in the repo and return the status."""
    try:
        # Get HEAD before pull
        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Run git pull
        subprocess.run(
            ["git", "pull"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )

        # Get HEAD after pull
        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        if head_before == head_after:
            return "up_to_date"

        return "updated"

    except subprocess.CalledProcessError as e:
        return f"error: {e.stderr.strip() if e.stderr else str(e)}"


def update_npx_skill(skill_name: str) -> str:
    """Update a skill installed via npx skills."""
    try:
        result = subprocess.run(
            ["npx", "skills", "update"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return "updated"
    except subprocess.CalledProcessError as e:
        return f"error: {e.stderr.strip() if e.stderr else str(e)}"
    except subprocess.TimeoutExpired:
        return "error: timeout"
    except FileNotFoundError:
        return "error: npx not found"


def get_all_updatable_skills():
    """
    Return a list of (skill_name, path, source_type, source_info, scope) for all updatable skills.
    """
    skills = []

    skills_with_sources = config.get_all_skills_with_sources()

    for name, info in sorted(skills_with_sources.items()):
        path = info["path"]
        source_type = info.get("source_type", config.SOURCE_TYPE_UNKNOWN)
        source_info = info.get("source_info", {})
        scope = info.get("scope", "unknown")

        skills.append((name, path, source_type, source_info, scope))

    return skills


def ask_skills_to_update(skills):
    """Interactive menu to select skills."""
    print("\n📦 Select skills to update:\n")

    # Categorize by source type
    npx_skills = []
    git_skills = []
    local_skills = []
    unknown_skills = []

    print("   Checking for updates (parallel)...")

    # Run git checks in parallel for git-based skills
    git_futures = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for name, path, source_type, source_info, scope in skills:
            if source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
                git_futures[name] = executor.submit(check_updates_available, path)

    for name, path, source_type, source_info, scope in skills:
        status_msg = ""
        has_update = False

        if name in git_futures:
            has_update, status_msg = git_futures[name].result()
        elif source_type == config.SOURCE_TYPE_NPX:
            status_msg = "Use 'npx skills update'"
        elif source_type == config.SOURCE_TYPE_LOCAL:
            status_msg = "Manual update required"
        else:
            status_msg = "Unknown source"

        # Add scope info to entry
        entry = (name, path, source_type, source_info, has_update, status_msg, scope)

        if source_type == config.SOURCE_TYPE_NPX:
            npx_skills.append(entry)
        elif source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
            git_skills.append(entry)
        elif source_type == config.SOURCE_TYPE_LOCAL:
            local_skills.append(entry)
        else:
            unknown_skills.append(entry)

    # Display Menu
    all_options = []
    idx = 1

    def get_scope_badge(scope):
        if scope == "global":
            return "[Global]"
        if scope == "project":
            return "[Project]"
        return ""

    if git_skills:
        print(f"\n   🔗 Git-based skills (updatable with git pull):")
        for (
            name,
            path,
            source_type,
            source_info,
            has_update,
            status_msg,
            scope,
        ) in git_skills:
            marker = "* " if has_update else "  "
            badge = get_scope_badge(scope)
            print(f"   {idx}. {marker}{name:25} {badge} [{status_msg}]")
            all_options.append((name, path, source_type, "git"))
            idx += 1

    if npx_skills:
        print(f"\n   📦 npx skills (use 'npx skills update' to update):")
        for (
            name,
            path,
            source_type,
            source_info,
            has_update,
            status_msg,
            scope,
        ) in npx_skills:
            source_repo = source_info.get("source", "") if source_info else ""
            print(f"   {idx}. {name:25} [{source_repo}]")
            all_options.append((name, path, source_type, "npx"))
            idx += 1

    if local_skills:
        print(f"\n   📁 Local skills (manual update required):")
        for (
            name,
            path,
            source_type,
            source_info,
            has_update,
            status_msg,
            scope,
        ) in local_skills:
            badge = get_scope_badge(scope)
            print(f"   {idx}. {name:25} {badge} [Local directory]")
            all_options.append((name, path, source_type, "local"))
            idx += 1

    if unknown_skills:
        print(f"\n   ❓ Unknown source:")
        for (
            name,
            path,
            source_type,
            source_info,
            has_update,
            status_msg,
            scope,
        ) in unknown_skills:
            badge = get_scope_badge(scope)
            print(f"   {idx}. {name:25} {badge} [Unknown]")
            all_options.append((name, path, source_type, "unknown"))
            idx += 1

    if not all_options:
        print("   No skills found.")
        return []

    print(f"\n   A. Update All Git-based skills")
    print(f"   N. Run 'npx skills update' for npx skills")

    choice = input(f"\nEnter choice (e.g. '1,2', 'A' for git, 'N' for npx): ").strip()

    if not choice:
        return []

    # Handle special cases
    if choice.lower() == "a" or "all" in choice.lower():
        return [
            (name, path, st, method)
            for name, path, st, method in all_options
            if method == "git"
        ]

    if choice.lower() == "n":
        return [("__npx_update__", None, config.SOURCE_TYPE_NPX, "npx")]

    selected = []

    # Handle ranges and commas
    parts = choice.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                for i in range(start, end + 1):
                    if 1 <= i <= len(all_options):
                        selected.append(all_options[i - 1])
            except ValueError:
                pass
        else:
            try:
                i = int(part)
                if 1 <= i <= len(all_options):
                    selected.append(all_options[i - 1])
            except ValueError:
                pass

    return selected


def main():
    parser = argparse.ArgumentParser(
        description="Update skills based on installation source."
    )
    parser.add_argument("skills", nargs="*", help="Specific skill names to update")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all Git-based skills without prompting",
    )
    parser.add_argument(
        "--npx",
        action="store_true",
        help="Run 'npx skills update' for npx-installed skills",
    )
    args = parser.parse_args()

    targets = []

    # Handle --npx flag
    if args.npx:
        print("\n📦 Running 'npx skills update'...\n")
        try:
            subprocess.run(["npx", "skills", "update"], check=True)
            print("\n✅ npx skills update complete!")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ npx skills update failed: {e}")
        except FileNotFoundError:
            print("\n❌ npx not found. Please install Node.js first.")
        return

    all_skills_map = config.get_all_skills_with_sources()

    # 1. Update specific skills from args
    if args.skills:
        for name in args.skills:
            if name not in all_skills_map:
                print(f"❌ Skill '{name}' not found.")
                continue

            info = all_skills_map[name]
            path = info["path"]
            source_type = info.get("source_type")

            if source_type == config.SOURCE_TYPE_NPX:
                print(f"📦 Skill '{name}' was installed via npx skills.")
                print(f"   Run 'npx skills update' to update it.")
                continue
            elif source_type == config.SOURCE_TYPE_LOCAL:
                print(f"📁 Skill '{name}' is a local skill (no git repo).")
                print(f"   Manual update required.")
                continue
            elif get_git_repo_status(path) != "git":
                print(f"⚠️  Skill '{name}' is not a git repository.")
                continue

            targets.append((name, path, source_type, "git"))

    # 2. Update all Git-based if --all flag
    elif args.all:
        all_skills = get_all_updatable_skills()
        for name, path, source_type, source_info, scope in all_skills:
            if source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
                targets.append((name, path, source_type, "git"))

    # 3. Interactive mode if no args
    else:
        all_skills = get_all_updatable_skills()
        if not all_skills:
            print("📭 No skills found to update.")
            return
        targets = ask_skills_to_update(all_skills)

    if not targets:
        print("No skills selected.")
        return

    # Check for npx update request
    if len(targets) == 1 and targets[0][0] == "__npx_update__":
        # Scan for npx skills to determine what to run
        has_global_npx = False
        has_project_npx = False

        # Check all skills to see if we have npx ones
        npx_skills_found = [
            s
            for s in config.get_all_skills_with_sources().values()
            if s.get("source_type") == config.SOURCE_TYPE_NPX
        ]

        for s in npx_skills_found:
            if s.get("scope") == "global":
                has_global_npx = True
            if s.get("scope") == "project":
                has_project_npx = True

        # If no npx skills found but user requested update, maybe they just want to update emptiness?
        # Default to global update if nothing found, just in case.
        if not npx_skills_found:
            has_global_npx = True

        if has_global_npx:
            print("\n📦 Running 'npx skills update -g' (Global)...")
            try:
                subprocess.run(["npx", "skills", "update", "-g"], check=True)
                print("✅ Global update complete.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Global update failed: {e}")
            except FileNotFoundError:
                print("❌ npx not found.")

        if has_project_npx:
            # For project updates, we need to be in the project root
            # config.PROJECT_ROOT should be correct
            print(
                f"\n🏠 Running 'npx skills update' (Project: {config.PROJECT_ROOT})..."
            )
            try:
                subprocess.run(
                    ["npx", "skills", "update"],
                    cwd=str(config.PROJECT_ROOT),
                    check=True,
                )
                print("✅ Project update complete.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Project update failed: {e}")
            except FileNotFoundError:
                print("❌ npx not found.")

        return

    # Filter to only git-updatable skills
    git_targets = [(n, p, st, m) for n, p, st, m in targets if m == "git"]

    if not git_targets:
        print("\n⚠️  No Git-based skills selected for update.")
        print("   For npx skills, use: npx skills update")
        print("   For local skills, update manually.")
        return

    print(f"\n🔄 Updating {len(git_targets)} Git-based skill(s)...\n")

    updated_count = 0

    for name, path, source_type, method in git_targets:
        result = update_git_repo(path)

        if result == "up_to_date":
            print(f"   ✅ {name:25} [Up to date]")
        elif result == "updated":
            print(f"   ⬇️  {name:25} [Updated successfully]")
            updated_count += 1
        else:
            print(f"   ❌ {name:25} [Update failed: {result}]")

    print(f"\n✨ Update complete. {updated_count} skills updated.")


if __name__ == "__main__":
    main()
