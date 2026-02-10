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
    """Interactive TUI menu to select skills for update."""
    # Try to import TUI
    sys.path.append(str(Path(__file__).parent))
    try:
        import tui
    except ImportError:
        tui = None

    if not tui:
        print("\n⚠️  TUI module missing. Falling back to simple default.")
        targets = []
        for name, path, source_type, source_info, scope in skills:
            if source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
                targets.append((name, path, source_type, "git"))
        return targets

    print("\n📦 Checking for updates (parallel)...")

    # Run git checks in parallel for git-based skills
    git_futures = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for name, path, source_type, source_info, scope in skills:
            if source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
                git_futures[name] = executor.submit(check_updates_available, path)

    # Prepare data for TUI
    git_skills = []
    npx_skills = []
    local_skills = []

    for name, path, source_type, source_info, scope in skills:
        status_msg = ""
        has_update = False

        if name in git_futures:
            has_update, status_msg = git_futures[name].result()
        elif source_type == config.SOURCE_TYPE_NPX:
            status_msg = "Managed via npx"
        elif source_type == config.SOURCE_TYPE_LOCAL:
            status_msg = "Manual update"
        else:
            status_msg = "Unknown"

        entry = {
            "name": name,
            "path": path,
            "source_type": source_type,
            "has_update": has_update,
            "status": status_msg,
            "scope": scope,
        }

        if source_type == config.SOURCE_TYPE_NPX:
            npx_skills.append(entry)
        elif source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
            git_skills.append(entry)
        else:
            local_skills.append(entry)

    # Build TUI Options
    options = []
    sections = []

    # Git Section
    if git_skills:
        sections.append({"title": "Git Repositories", "start_index": len(options)})
        # Sort by update availability first, then name
        git_skills.sort(key=lambda x: (not x["has_update"], x["name"]))

        for s in git_skills:
            label = f"{s['name']}"
            if s["has_update"]:
                label += f" \033[33m(Update Available)\033[0m"
            else:
                label += f" \033[2m({s['status']})\033[0m"

            options.append(
                {
                    "id": f"git:{s['name']}",
                    "label": label,
                    "checked": s["has_update"],  # Default check if update available
                    "raw": (s["name"], s["path"], s["source_type"], "git"),
                }
            )

    # npx Section
    if npx_skills:
        sections.append({"title": "npx Skills", "start_index": len(options)})

        options.append(
            {
                "id": "__npx_update__",
                "label": "Update all npx skills (via 'npx skills update')",
                "checked": False,
                "raw": ("__npx_update__", None, config.SOURCE_TYPE_NPX, "npx"),
            }
        )

        for s in npx_skills:
            options.append(
                {
                    "id": f"npx:{s['name']}",
                    "label": f"{s['name']}",
                    "checked": True,
                    "disabled": True,  # Info only
                }
            )

    # Local Section
    if local_skills:
        sections.append({"title": "Local / Manual", "start_index": len(options)})
        for s in local_skills:
            options.append(
                {
                    "id": f"local:{s['name']}",
                    "label": f"{s['name']} ({s['status']})",
                    "checked": False,
                    "disabled": True,
                }
            )

    if not options:
        print("   No skills found.")
        return []

    menu = tui.MultiSelectMenu("Select skills to update", options, sections)
    print("\033[2m  ↑↓ move, space select, enter confirm\033[0m")

    try:
        selected_ids = menu.run()
    except KeyboardInterrupt:
        return []

    # Map results
    results = []

    # Helper to find raw data
    results_map = {opt["id"]: opt.get("raw") for opt in options}

    for sid in selected_ids:
        raw = results_map.get(sid)
        if raw:
            results.append(raw)

    return results


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

    # Determine mode
    non_interactive = args.npx or args.all or args.skills

    # 1. Handle --npx flag
    if args.npx:
        print("\n📦 Running 'npx skills update'...\n")
        try:
            subprocess.run(["npx", "skills", "update"], check=True)
            print("\n✅ npx skills update complete!")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ npx skills update failed: {e}")
        except FileNotFoundError:
            print("\n❌ npx not found. Please install Node.js first.")

    # 2. Identify Git targets
    targets = []
    all_skills_map = config.get_all_skills_with_sources()

    if args.skills:
        for name in args.skills:
            if name not in all_skills_map:
                print(f"❌ Skill '{name}' not found.")
                continue

            info = all_skills_map[name]
            path = info["path"]
            source_type = info.get("source_type")

            if source_type == config.SOURCE_TYPE_NPX:
                # If user specifically asked for an npx skill by name, remind them
                if not args.npx:
                    print(f"📦 Skill '{name}' is an npx skill.")
                    print(f"   Run with --npx to update.")
                continue
            elif source_type == config.SOURCE_TYPE_LOCAL:
                print(f"📁 Skill '{name}' is a local skill (no git repo).")
                print(f"   Manual update required.")
                continue
            elif get_git_repo_status(path) != "git":
                print(f"⚠️  Skill '{name}' is not a git repository.")
                continue

            targets.append((name, path, source_type, "git"))

    elif args.all:
        all_skills = get_all_updatable_skills()
        for name, path, source_type, source_info, scope in all_skills:
            if source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
                targets.append((name, path, source_type, "git"))

    # 3. Interactive mode (only if no flags set)
    elif not non_interactive:
        all_skills = get_all_updatable_skills()
        if not all_skills:
            print("📭 No skills found to update.")
            return
        targets = ask_skills_to_update(all_skills)

    if not targets and not args.npx:
        # If we didn't run npx and selected no targets, exit
        print("No skills selected.")
        return
    elif not targets:
        # We ran npx but have no git targets, we are done
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
