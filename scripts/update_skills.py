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


def update_git_subdir_skill(
    skill_path: Path, source_url: str, source_subdir: str
) -> tuple[str, str]:
    """
    更新从多 skill repo 子目录安装的 skill。
    通过重新 clone 整个 repo，提取指定子目录来更新。
    返回: (status, new_commit_hash)
    """
    import tempfile
    import shutil

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        temp_clone = Path(temp_dir) / "repo"

        # Clone 整个 repo
        subprocess.run(
            ["git", "clone", "--depth", "1", source_url, str(temp_clone)],
            check=True,
            capture_output=True,
            timeout=60,
        )

        # 获取新的 commit hash
        new_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(temp_clone),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # 检查子目录是否存在
        subdir_path = temp_clone / source_subdir
        if not subdir_path.exists():
            return f"error: subdir '{source_subdir}' not found in cloned repo", ""

        # 替换现有 skill 目录（保留 .git 目录如果有的话）
        if skill_path.exists():
            shutil.rmtree(skill_path)
        shutil.copytree(subdir_path, skill_path)

        return "updated", new_hash

    except subprocess.CalledProcessError as e:
        return (
            f"error: git clone failed - {e.stderr.decode().strip() if e.stderr else str(e)}",
            "",
        )
    except subprocess.TimeoutExpired:
        return "error: timeout during clone", ""
    except Exception as e:
        return f"error: {str(e)}", ""
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def check_subdir_updates_available(
    source_url: str, skill_path: Path, source_subdir: str, local_hash: str = None
) -> tuple[bool, str]:
    """
    检查子目录类型 skill 是否有可用更新。
    对比远程 HEAD hash 和本地 metadata 中的 hash。
    """
    try:
        # 获取远程 HEAD hash
        remote_output = subprocess.run(
            ["git", "ls-remote", source_url, "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()

        if not remote_output:
            return False, "Unknown remote"

        remote_hash = remote_output.split()[0]

        if local_hash and remote_hash == local_hash:
            return False, "Up to date"

        return True, f"📦 Update available ({remote_hash[:7]})"

    except Exception as e:
        return True, f"📦 Check failed (assuming update avail)"


def get_all_updatable_skills(scope: str = None):
    """
    Return a list of (skill_name, path, source_type, source_info, scope) for updatable skills.
    """
    skills = []

    skills_with_sources = config.get_all_skills_with_sources(scope=scope)

    for name, info in sorted(skills_with_sources.items()):
        # Handle original_name if it was a collision key
        skill_name = info.get("original_name", name)
        path = info["path"]
        source_type = info.get("source_type", config.SOURCE_TYPE_UNKNOWN)
        source_info = info.get("source_info", {})
        scope_val = info.get("scope", "unknown")

        skills.append((skill_name, path, source_type, source_info, scope_val))

    return skills


def ask_skills_to_update(skills, selected_scope: str):
    """Interactive TUI menu to select skills for update."""
    title = f"Select skills to update ({selected_scope.capitalize()})"
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
                targets.append((name, path, source_type, "git", scope))
        return targets

    print("\n📦 Checking for updates (parallel)...")

    # Run checks in parallel for git-based skills
    git_futures = {}
    subdir_skills_info = {}  # 子目录类型 skill 的信息
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for name, path, source_type, source_info, scope in skills:
            source_subdir = (
                source_info.get("source_subdir")
                if isinstance(source_info, dict)
                else None
            )
            if source_subdir and source_type == config.SOURCE_TYPE_GIT:
                # 子目录类型：无法用 git fetch 检查，但标记为可更新
                source_url = source_info.get("source_url", "")
                commit_hash = source_info.get("commit_hash", None)
                subdir_skills_info[name] = {
                    "source_url": source_url,
                    "source_subdir": source_subdir,
                    "commit_hash": commit_hash,
                }
                git_futures[name] = executor.submit(
                    check_subdir_updates_available,
                    source_url,
                    path,
                    source_subdir,
                    commit_hash,
                )
            elif source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
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

    # Filter Git Skills (Only show updates)
    updatable_git_skills = [s for s in git_skills if s["has_update"]]

    # Git Section
    if updatable_git_skills:
        sections.append({"title": "Git Repositories", "start_index": len(options)})
        # Sort by name (since all have update available)
        updatable_git_skills.sort(key=lambda x: x["name"])

        for s in updatable_git_skills:
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
                    "raw": (
                        s["name"],
                        s["path"],
                        s["source_type"],
                        "git_subdir" if s["name"] in subdir_skills_info else "git",
                        s["scope"],
                    ),
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
                "raw": (
                    "__npx_update__",
                    None,
                    config.SOURCE_TYPE_NPX,
                    "npx",
                    "global",
                ),
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
        print("\n✅ All tracked skills are up to date!")
        return []

    menu = tui.MultiSelectMenu(title, options, sections)

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
    parser.add_argument(
        "--scope",
        choices=["global", "project"],
        default=None,
        help="Target scope (skip TUI scope selection in interactive mode)",
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
        # Handle each requested skill
        for name in args.skills:
            # Use find_installed_skill for robust lookup (supports hierarchical paths)
            selected_info = config.find_installed_skill(name, scope=args.scope)

            if not selected_info:
                print(f"❌ Skill '{name}' not found.")
                continue

            path = selected_info["path"]
            source_type = selected_info.get("source_type")
            scope = selected_info.get("scope", "global")

            # 检查是否是子目录类型的 git skill
            source_info = selected_info.get("source_info", {})
            source_subdir = (
                source_info.get("source_subdir")
                if isinstance(source_info, dict)
                else None
            )

            if source_type == config.SOURCE_TYPE_NPX:
                print(f"📦 Skill '{name}' is an npx skill (Scope: {scope}).")
                # ... resto de la lógica de npx ...
                if scope == "global":
                    print("   Running 'npx skills update -g' (Global)...")
                    try:
                        subprocess.run(["npx", "skills", "update", "-g"], check=True)
                        print(
                            f"✅ Global Registry update complete (includes '{name}')."
                        )
                    except Exception as e:
                        print(f"❌ Global update failed: {e}")
                else:
                    print(
                        f"   Running 'npx skills update' (Project: {config.PROJECT_ROOT})..."
                    )
                    try:
                        subprocess.run(
                            ["npx", "skills", "update"],
                            cwd=str(config.PROJECT_ROOT),
                            check=True,
                        )
                        print(
                            f"✅ Project Registry update complete (includes '{name}')."
                        )
                    except Exception as e:
                        print(f"❌ Project update failed: {e}")
                continue
            elif source_type == config.SOURCE_TYPE_LOCAL:
                print(f"📁 Skill '{name}' is a local skill (no git repo).")
                print(f"   Manual update required.")
                continue

            # 检查是否是子目录类型的 git skill
            source_info = selected_info.get("source_info", {})
            source_subdir = (
                source_info.get("source_subdir")
                if isinstance(source_info, dict)
                else None
            )
            if source_subdir and source_type == config.SOURCE_TYPE_GIT:
                targets.append((name, path, source_type, "git_subdir", scope))
                continue

            if get_git_repo_status(path) != "git":
                print(f"⚠️  Skill '{name}' is not a git repository.")
                continue

            targets.append((name, path, source_type, "git", scope))

    elif args.all:
        all_skills = get_all_updatable_skills()
        for name, path, source_type, source_info, scope in all_skills:
            source_subdir = (
                source_info.get("source_subdir")
                if isinstance(source_info, dict)
                else None
            )
            if source_subdir and source_type == config.SOURCE_TYPE_GIT:
                targets.append((name, path, source_type, "git_subdir", scope))
            elif source_type == config.SOURCE_TYPE_GIT or (path / ".git").exists():
                targets.append((name, path, source_type, "git", scope))

    # 3. Interactive mode (only if no flags set)
    elif not non_interactive:
        # Interactive mode—需要选择 scope
        if args.scope:
            selected_scope = args.scope
        else:
            selected_scope = config.ask_scope_tui("Which scope do you want to update?")
        all_skills = get_all_updatable_skills(scope=selected_scope)

        if not all_skills:
            print(f"📭 No skills found to update in {selected_scope} scope.")
            return
        targets = ask_skills_to_update(all_skills, selected_scope)

    if not targets and not args.npx:
        # If we didn't run npx and selected no targets, exit
        print("No skills selected.")
        return
    elif not targets:
        # We ran npx but have no git targets, we are done
        return

    # Check for npx update request
    npx_update_requested = any(t[0] == "__npx_update__" for t in targets)
    if npx_update_requested:
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

    # Filter to git-updatable and subdir-updatable skills
    git_targets = [t for t in targets if len(t) == 5 and t[3] in ("git", "git_subdir")]

    if not git_targets:
        print("\n⚠️  No Git-based skills selected for update.")
        print("   For npx skills, use: npx skills update")
        print("   For local skills, update manually.")
        return

    print(f"\n🔄 Updating {len(git_targets)} Git-based skill(s)...\n")

    updated_count = 0

    for name, path, source_type, method, scope in git_targets:
        if method == "git_subdir":
            # 子目录类型：需要从 metadata 获取 source_url 和 source_subdir
            skill_meta = config.load_metadata(scope).get(name, {})
            source_url = skill_meta.get("source_url", "")
            source_subdir = skill_meta.get("source_subdir", "")
            if not source_url or not source_subdir:
                print(
                    f"   ❌ {name:25} [Missing source_url or source_subdir in metadata]"
                )
                continue

            # Check updates first
            local_hash = skill_meta.get("commit_hash")
            update_needed, msg = check_subdir_updates_available(
                source_url, path, source_subdir, local_hash
            )

            if not update_needed:
                result = "up_to_date"
                new_hash = local_hash
            else:
                # 执行更新
                result, new_hash = update_git_subdir_skill(
                    path, source_url, source_subdir
                )

            # 如果更新成功且有新 hash，更新 metadata
            if result == "updated" and new_hash:
                # 重新加载 metadata 以防并发修改（尽管这里是串行）
                md = config.load_metadata(scope)
                if name in md:
                    md[name]["commit_hash"] = new_hash
                    config.save_metadata(md, scope)

                # Metadata updated
        else:
            result = update_git_repo(path)

        if result == "up_to_date":
            # print(f"   ✅ {name:25} [Up to date]")
            pass
        elif result == "updated":
            print(f"   ⬇️  {name:25} [Updated successfully]")
            updated_count += 1
        else:
            print(f"   ❌ {name:25} [Update failed: {result}]")

    print(f"\n✨ Update complete. {updated_count} skills updated.")


if __name__ == "__main__":
    main()
