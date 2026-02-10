#!/usr/bin/env python3
"""
Install a skill to the central repository (.agents/skills) and sync to detected agent platforms via symlinks.
Supports installing from local path or Git URL, and supports Global or Project scopes.
"""

import os
import sys
import shutil
import json
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

# Import central configuration
import config


def get_skill_name_from_url(url: str) -> str:
    """Extract skill name from Git URL."""
    # Remove .git extension if present
    name = url.split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def clone_git_repo(url: str, target_dir: Path) -> Path:
    """Clone a git repository to a target directory."""
    print(f"   ⬇️  Cloning from {url}...")
    try:
        # ensuring parent dir exists
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["git", "clone", url, str(target_dir)], check=True, capture_output=True
        )
        return target_dir
    except subprocess.CalledProcessError as e:
        print(f"❌ Error cloning repository: {e.stderr.decode().strip()}")
        sys.exit(1)


def install_via_npx(skill_name: str, scope: str = "project") -> bool:
    """Install a skill via npx skills add."""
    cmd = ["npx", "skills", "add", skill_name, "-y"]
    if scope == "global":
        cmd.append("-g")

    print(f"   ⚙️  Running '{' '.join(cmd)}'...")
    try:
        # For project scope, we should be in PROJECT_ROOT
        cwd = str(config.PROJECT_ROOT) if scope == "project" else None
        subprocess.run(cmd, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("   ❌ npx not found. Cannot install via Registry.")
        return False


def get_skill_name(skill_path: Path) -> str:
    """Extract skill name from path or SKILL.md."""
    # If it's a .skill file, use the filename
    if skill_path.suffix == ".skill":
        return skill_path.stem

    # If it's a directory, use the directory name
    if skill_path.is_dir():
        return skill_path.name

    raise ValueError(f"Invalid skill path: {skill_path}")


def unzip_skill_file(skill_file: Path, target_dir: Path) -> Path:
    """Unzip .skill file to target directory."""
    import zipfile

    skill_name = skill_file.stem
    extract_path = target_dir / skill_name

    with zipfile.ZipFile(skill_file, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    return extract_path


def get_platform_paths(scope: str) -> dict:
    """
    Get available platforms with appropriate paths.
    If scope is 'project', returns paths relative to CWD.
    If 'global', returns global system paths.
    """
    if scope == "global":
        return config.get_available_platforms()

    # improved local install scanning
    available = {}
    cwd = config.PROJECT_ROOT

    for name, conf in config.SUPPORTED_PLATFORMS.items():
        local_rel_path = conf["local"]
        local_full_path = cwd / local_rel_path

        # We consider it available if the parent config dir exists (e.g. .claude exists for .claude/skills)
        # OR if it's just a standard structure we want to enforce.
        # For simplicity, let's mirror the global logic: check if parent exists.

        parent_dir = local_full_path.parent
        # Also check if parent itself exists, if local_rel_path is deep
        # e.g. .agent/skills -> check .agent exists

        if parent_dir.exists():
            available[conf["id"]] = {
                "name": name,
                "path": local_full_path,
                "is_local": True,
            }

    return available


def check_conflicts(
    skill_name: str, available_platforms: dict, scope: str = "global"
) -> dict:
    """Check if skill already exists in repo or platforms (as non-symlink)."""
    conflicts = {}
    repo_path = config.get_skill_repo(scope)

    # Check repo
    if (repo_path / skill_name).exists():
        conflicts["repo"] = repo_path / skill_name

    # Check available platforms for conflicts
    for p_id, info in available_platforms.items():
        target = info["path"] / skill_name
        if target.exists():
            # If it's a symlink pointing to our repo, it's not a conflict, it's just an update
            if (
                target.is_symlink()
                and target.resolve() == (repo_path / skill_name).resolve()
            ):
                continue
            conflicts[info["name"]] = target

    return conflicts


def ask_user_overwrite(conflicts: dict) -> bool:
    """Ask user whether to overwrite existing skills."""
    print("\n⚠️  Conflicts detected:")
    for platform, path in conflicts.items():
        is_symlink = path.is_symlink()
        link_target = f" → {path.resolve()}" if is_symlink else ""
        type_str = "symlink" if is_symlink else "directory/file"
        print(f"   - {platform}: {path} ({type_str}{link_target})")

    response = input("\nOverwrite existing installations? [y/N]: ").strip().lower()
    return response == "y"


def install_to_repo(
    source_path: Path,
    skill_name: str,
    scope: str = "global",
    force: bool = False,
    is_git: bool = False,
) -> Path:
    """Install skill to correct Skill Repo (Global or Project)."""
    repo_path = config.get_skill_repo(scope)
    target_path = repo_path / skill_name

    # Create repo directory if it doesn't exist
    repo_path.mkdir(parents=True, exist_ok=True)

    # Remove existing if force
    if target_path.exists() and force:
        if target_path.is_symlink():
            target_path.unlink()
        else:
            shutil.rmtree(target_path)

    # Copy/Move skill to Repo
    if is_git:
        # If it was a git clone, we already have it in a temp dir or target dir
        # If source_path is the temp dir, move it
        # We need to make sure we're not moving to ourselves if something weird happened
        if source_path.resolve() != target_path.resolve():
            shutil.move(str(source_path), str(target_path))
        return target_path

    if source_path.is_file() and source_path.suffix == ".skill":
        # Unzip .skill file
        return unzip_skill_file(source_path, repo_path)
    else:
        # Copy directory
        # If source is same as target (re-installing from repo), skip copy
        if source_path.resolve() == target_path.resolve():
            return target_path

        shutil.copytree(source_path, target_path, dirs_exist_ok=force)
        return target_path


def create_symlink(source: Path, target: Path, force: bool = False):
    """Create symlink from target to source."""
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        if not force:
            print(f"   ⚠️  Skipping {target} (exists, use force to overwrite)")
            return

        if target.is_symlink():
            target.unlink()
        else:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

    target.symlink_to(source)


# Using config.ask_scope_tui instead


def ask_sync_targets(available_platforms: dict, is_local: bool) -> list[str]:
    """Ask user which platforms to sync to based on available platforms using TUI."""
    if not available_platforms:
        if is_local:
            print("\n⚠️  No local project configuration found in current directory.")
            print("   (Expected folders like .claude, .chat, .agent, etc.)")
        else:
            print("\n⚠️  No supported platforms detected on this system.")
        return []

    # Try to import TUI (local project script)
    try:
        import tui
    except ImportError:
        # Fallback if tui.py missing (try adding current dir to path)
        sys.path.append(str(Path(__file__).parent))
        try:
            import tui
        except ImportError:
            tui = None

    if not tui:
        print("\n⚠️  TUI module missing. Using default selection (All).")
        return list(available_platforms.keys())

    # Group platforms
    universal_targets = []
    other_targets = []

    for p_id, info in available_platforms.items():
        # Check if Universal (.agents/skills)
        path_str = str(info["path"])

        # Heuristic: ends with .agents/skills or .agent/skills?
        if ".agents/skills" in path_str:
            universal_targets.append((p_id, info))
        else:
            other_targets.append((p_id, info))

    # Construct TUI options
    options = []
    sections = []

    # 1. Universal Section
    if universal_targets:
        sections.append(
            {
                "title": f"Universal ({config.SKILL_REPO_PROJECT.name if is_local else '.agents/skills'})",
                "start_index": len(options),
            }
        )

        # Sort Universal items alphabetically
        universal_targets.sort(key=lambda x: x[1]["name"])

        for p_id, info in universal_targets:
            options.append(
                {
                    "id": p_id,
                    "label": f"{info['name']}",
                    "checked": True,  # Default On for universal
                    "disabled": True,  # Fixed, cannot be unchecked
                }
            )

    # 2. Others Section
    if other_targets:
        sections.append({"title": "Other agents", "start_index": len(options)})

        # Sort Others alphabetically
        other_targets.sort(key=lambda x: x[1]["name"])

        for p_id, info in other_targets:
            display_path = info["path"]
            if is_local:
                try:
                    display_path = info["path"].relative_to(config.PROJECT_ROOT)
                except ValueError:
                    pass

            options.append(
                {
                    "id": p_id,
                    "label": f"{info['name']} ({display_path})",
                    "checked": False,  # Default Off for others?
                }
            )

    menu = tui.MultiSelectMenu(
        "Which agents do you want to install to?", options, sections
    )

    # Instructions Footer

    try:
        selected_ids = menu.run()
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
        sys.exit(0)

    # Calculate summary for display
    print(f"\n✅ Selected: {len(selected_ids)} agents")
    return selected_ids


def sync_to_platforms(
    repo_skill_path: Path,
    skill_name: str,
    selected_ids: list[str],
    available_platforms: dict,
    force: bool = False,
):
    """Create symlinks in selected platforms."""
    print(f"\n📎 Creating symlinks from {repo_skill_path}...")

    if not selected_ids:
        print("   No platforms selected.")
        return

    for p_id in selected_ids:
        if p_id in available_platforms:
            info = available_platforms[p_id]
            target = info["path"] / skill_name
            create_symlink(repo_skill_path, target, force)
            print(f"   ✅ {info['name']}: {target}")


def update_sync_metadata(
    skill_name: str,
    selected_ids: list[str],
    available_platforms: dict,
    scope: str = "global",
    source_type: str = "unknown",
    source_url: Optional[str] = None,
):
    """Update metadata file with sync information."""
    metadata = config.load_metadata(scope)
    repo_path = config.get_skill_repo(scope)

    # We need to preserve global targets if we are installing local, and vice versa
    # Actually, simplistic approach: just append to the list of targets if not present.

    current_targets = set(metadata.get(skill_name, {}).get("targets", []))

    new_targets = []
    for p_id in selected_ids:
        if p_id in available_platforms:
            new_targets.append(str(available_platforms[p_id]["path"] / skill_name))

    # Merge
    current_targets.update(new_targets)

    # Filter out non-existent
    valid_targets = []
    for t in current_targets:
        if os.path.exists(t) or os.path.islink(t):
            valid_targets.append(t)

    metadata[skill_name] = {
        "source": str(repo_path / skill_name),
        "source_type": source_type,
        "source_url": source_url,
        "targets": valid_targets,
    }
    config.save_metadata(metadata, scope)


def main():
    parser = argparse.ArgumentParser(
        description="Install a skill to skill_repo and sync to platforms."
    )
    parser.add_argument(
        "skill_path", help="Path to local skill, .skill file, or Git URL"
    )
    parser.add_argument(
        "--scope",
        choices=["global", "project"],
        default=None,
        help="Installation scope: Auto-detect (default), 'global', or 'project'",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Deprecated alias for --scope project",
    )

    args = parser.parse_args()

    # Handle deprecated --local flag
    if args.local:
        if args.scope and args.scope != "global":
            # If someone explicitly says --scope global --local, that's weird, but prioritize local flag?
            # Or scope? The original code prioritized local.
            pass
        # If scope is Global, warn? Original code warned.
        if args.scope == "global":
            print(
                "⚠️  Warning: Both --local and --scope provided. Using --local (project scope)."
            )
        args.scope = "project"

    # Auto-detect scope if not provided
    if args.scope is None:
        args.scope = config.ask_scope_tui("Installation scope")

    source_input = args.skill_path
    is_git = False
    is_npx = False
    temp_dir = None
    source_path = None
    skill_name = None

    try:
        # Detect if Git URL
        if source_input.startswith("http") or source_input.startswith("git@"):
            is_git = True
            skill_name = get_skill_name_from_url(source_input)
            print(f"📦 Detected Git URL for skill: {skill_name}")

            # Determine strict source path (temp or direct to repo?)
            # To handle conflicts properly, let's clone to a temp dir first
            temp_dir = tempfile.mkdtemp()
            # The clone will create the subdir inside temp_dir
            source_path = clone_git_repo(source_input, Path(temp_dir) / skill_name)
        else:
            source_path = Path(source_input).resolve()
            if not source_path.exists():
                # Potential Community Registry Skill
                print(
                    f"🔍 Path '{source_input}' not found. Trying Community Registry..."
                )
                skill_name = source_input
                if install_via_npx(skill_name, args.scope):
                    # If successful, the skill is now in the repo
                    is_npx = True
                    source_path = config.get_skill_repo(args.scope) / skill_name
                    print(f"✅ Successfully installed '{skill_name}' via Registry!")
                else:
                    print(
                        f"❌ Error: '{source_input}' is not a valid path, Git URL, or Registry skill."
                    )
                    sys.exit(1)
            else:
                skill_name = get_skill_name(source_path)
                print(f"📦 Installing skill: {skill_name}")
                print(f"   Source: {source_path}")

        # Check if source is already inside a managed repo
        is_inside_global = False
        try:
            # is_relative_to is Python 3.9+
            if source_path.is_relative_to(config.SKILL_REPO_GLOBAL.resolve()):
                is_inside_global = True
        except Exception:
            pass

        is_inside_project = False
        if config.SKILL_REPO_PROJECT.exists():
            try:
                if source_path.is_relative_to(config.SKILL_REPO_PROJECT.resolve()):
                    is_inside_project = True
            except Exception:
                pass

        if is_inside_global or is_inside_project:
            repo_name = "Global" if is_inside_global else "Project"
            print(
                f"\n⚠️  Action Aborted: Source path is already inside managed {repo_name} Repo."
            )
            print(f"   Path: {source_path}")
            print(
                f"   - To link/sync to more agents: python3 scripts/sync_skill.py {skill_name}"
            )
            print(f"   - To update code: python3 scripts/update_skills.py")
            sys.exit(0)

        # Determine target platforms (Global vs Local)
        available_platforms = get_platform_paths(args.scope)
        repo_path_root = config.get_skill_repo(args.scope)

        # Check for conflicts
        conflicts = check_conflicts(skill_name, available_platforms, args.scope)
        force = False

        # Filter out self-conflicts if reinstalling from repo
        if not is_git and source_path == repo_path_root / skill_name:
            conflicts.pop("repo", None)

        if conflicts:
            if not ask_user_overwrite(conflicts):
                print("\n❌ Installation cancelled.")
                sys.exit(0)
            force = True

        # Install to Central Repo
        print(f"\n📥 Installing to '{args.scope}' Repo ({repo_path_root})...")
        repo_path = install_to_repo(
            source_path, skill_name, scope=args.scope, force=force, is_git=is_git
        )
        print(f"   ✅ Stored at: {repo_path}")

        # Ask user which platforms to sync
        sync_targets = ask_sync_targets(available_platforms, args.scope == "project")

        # Sync to platforms
        sync_to_platforms(
            repo_path, skill_name, sync_targets, available_platforms, force
        )

        # Update metadata
        # Detect if it's a local git repo even if installed from path
        final_source_type = config.SOURCE_TYPE_LOCAL
        if is_npx:
            final_source_type = config.SOURCE_TYPE_NPX
        elif is_git:
            final_source_type = config.SOURCE_TYPE_GIT
        elif (repo_path / ".git").exists():
            # If we copied a .git folder, it's a git repo
            final_source_type = config.SOURCE_TYPE_GIT
            print(f"   ℹ️  Marked as Git repository (updates enabled).")

        update_sync_metadata(
            skill_name,
            sync_targets,
            available_platforms,
            scope=args.scope,
            source_type=final_source_type,
            source_url=source_input,
        )

        print(f"\n✅ Skill '{skill_name}' setup complete!")

    finally:
        # Cleanup temp if used
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
