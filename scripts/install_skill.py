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


def analyze_repo_structure(cloned_path: Path) -> dict:
    """
    分析 clone 后的 repo 结构，检测 skill 目录和安装说明。
    返回: {
        "type": "single" | "multi" | "no_skill",
        "skill_roots": [Path, ...],      # 包含 SKILL.md 的目录列表
        "readmes": [Path, ...],           # README 文件列表
        "root_has_skill": bool,           # 根目录是否有 SKILL.md
    }
    """
    skill_roots = []
    readmes = []

    # 使用 os.walk 搜索 SKILL.md（高效跳过 .git 和 node_modules 目录）
    for dirpath, dirnames, filenames in os.walk(cloned_path):
        # 就地修改 dirnames 以跳过不需要遍历的目录
        dirnames[:] = [
            d for d in dirnames if d not in (".git", "node_modules", "__pycache__")
        ]
        if "SKILL.md" in filenames:
            skill_roots.append(Path(dirpath))

    # 收集 README 文件（仅根目录和一级子目录）
    for readme_name in ["README.md", "README_CN.md", "README.rst", "readme.md"]:
        root_readme = cloned_path / readme_name
        if root_readme.exists():
            readmes.append(root_readme)

    root_has_skill = cloned_path in skill_roots

    if root_has_skill:
        repo_type = "single"
    elif skill_roots:
        repo_type = "multi"
    else:
        repo_type = "no_skill"

    return {
        "type": repo_type,
        "skill_roots": skill_roots,
        "readmes": readmes,
        "root_has_skill": root_has_skill,
    }


def print_readme_content(readme_path: Path, max_lines: int = 100):
    """输出 README 内容供 Agent 阅读。"""
    print(f"\n{'='*60}")
    print(f"📖 Repository README: {readme_path.name}")
    print(f"{'='*60}\n")
    try:
        content = readme_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) > max_lines:
            print("\n".join(lines[:max_lines]))
            print(f"\n... (截断，共 {len(lines)} 行，已显示前 {max_lines} 行)")
        else:
            print(content)
    except Exception as e:
        print(f"❌ 无法读取 README: {e}")
    print(f"\n{'='*60}")


def ask_skill_selection(skill_roots: list[Path], cloned_path: Path) -> list[Path]:
    """通过 TUI 让用户选择要安装的 skill 子目录。"""
    # 导入 TUI
    try:
        import tui
    except ImportError:
        sys.path.append(str(Path(__file__).parent))
        try:
            import tui
        except ImportError:
            tui = None

    if not tui or len(skill_roots) == 1:
        # 无 TUI 或仅一个 skill，直接返回
        return skill_roots

    options = []
    for root in sorted(skill_roots, key=lambda p: str(p)):
        try:
            rel_path = root.relative_to(cloned_path)
        except ValueError:
            rel_path = root

        # 尝试从 SKILL.md 的 frontmatter 读取名称和描述
        skill_md = root / "SKILL.md"
        skill_label = str(rel_path)
        try:
            content = skill_md.read_text(encoding="utf-8")
            # 简易解析 YAML frontmatter 中的 name 和 description
            if content.startswith("---"):
                end = content.index("---", 3)
                frontmatter = content[3:end]
                for line in frontmatter.splitlines():
                    line = line.strip()
                    if line.startswith("name:"):
                        name = line[5:].strip().strip('"').strip("'")
                        skill_label = f"{name} ({rel_path})"
                        break
        except Exception:
            pass

        options.append(
            {
                "id": str(root),
                "label": skill_label,
                "checked": True,
            }
        )

    menu = tui.MultiSelectMenu("Repo 中包含多个 Skills，请选择要安装的:", options)
    try:
        selected_ids = menu.run()
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
        sys.exit(0)

    return [Path(sid) for sid in selected_ids]


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
    source_subdir: Optional[str] = None,
    commit_hash: Optional[str] = None,
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
        "source_subdir": source_subdir,
        "commit_hash": commit_hash,
        "targets": valid_targets,
    }
    config.save_metadata(metadata, scope)


def _install_single_skill(
    source_path: Path,
    skill_name: str,
    scope: str,
    is_git: bool = False,
    source_url: Optional[str] = None,
    source_subdir: Optional[str] = None,
    commit_hash: Optional[str] = None,
):
    """
    安装单个 skill 的完整流程（从 conflict 检查到 sync）。
    提取为独立函数以支持多 skill repo 的逐个安装。
    """
    available_platforms = get_platform_paths(scope)
    repo_path_root = config.get_skill_repo(scope)

    # 冲突检测
    conflicts = check_conflicts(skill_name, available_platforms, scope)
    force = False
    if conflicts:
        if not ask_user_overwrite(conflicts):
            print(f"   ⏭️  Skipping '{skill_name}'.")
            return
        force = True

    # 安装到 Repo
    print(f"   📥 Installing to '{scope}' Repo ({repo_path_root})...")
    repo_path = install_to_repo(
        source_path, skill_name, scope=scope, force=force, is_git=is_git
    )
    print(f"   ✅ Stored at: {repo_path}")

    # 选择同步目标
    sync_targets = ask_sync_targets(available_platforms, scope == "project")

    # 同步到平台
    sync_to_platforms(repo_path, skill_name, sync_targets, available_platforms, force)

    # 更新 metadata
    final_source_type = config.SOURCE_TYPE_LOCAL
    if is_git:
        final_source_type = config.SOURCE_TYPE_GIT
    elif (repo_path / ".git").exists():
        final_source_type = config.SOURCE_TYPE_GIT

    update_sync_metadata(
        skill_name,
        sync_targets,
        available_platforms,
        scope=scope,
        source_type=final_source_type,
        source_url=source_url,
        source_subdir=source_subdir,
        commit_hash=commit_hash,
    )

    print(f"   ✅ Skill '{skill_name}' setup complete!")


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

            # Clone 到临时目录
            temp_dir = tempfile.mkdtemp()
            cloned_path = clone_git_repo(source_input, Path(temp_dir) / skill_name)

            # 获取当前 Commit Hash
            try:
                current_hash = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(cloned_path),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            except Exception:
                current_hash = None

            # === Repo 结构分析阶段 ===
            print("\n🔍 Analyzing repository structure...")
            analysis = analyze_repo_structure(cloned_path)

            if analysis["type"] == "single":
                # 纯 skill repo：根目录就是 SKILL.md，保持原有行为
                print(f"   ✅ Pure skill repo detected (root SKILL.md found).")
                source_path = cloned_path

            elif analysis["type"] == "multi":
                # 多 skill repo：子目录中有 SKILL.md
                print(
                    f"   📦 Found {len(analysis['skill_roots'])} skill(s) in subdirectories:"
                )
                for root in analysis["skill_roots"]:
                    try:
                        rel = root.relative_to(cloned_path)
                    except ValueError:
                        rel = root
                    print(f"      - {rel}/")

                # 如果 repo 有 README，也输出提示
                if analysis["readmes"]:
                    print_readme_content(analysis["readmes"][0])

                # 让用户选择要安装的 skill
                selected = ask_skill_selection(analysis["skill_roots"], cloned_path)

                if not selected:
                    print("\n❌ No skills selected. Installation cancelled.")
                    sys.exit(0)

                # 多 skill 逐个安装
                if len(selected) >= 1:
                    for i, skill_dir in enumerate(selected):
                        sub_skill_name = skill_dir.name
                        print(f"\n{'─'*40}")
                        print(
                            f"📦 [{i+1}/{len(selected)}] Installing skill: {sub_skill_name}"
                        )

                        # 计算子目录相对路径，供更新时使用
                        try:
                            subdir_rel = str(skill_dir.relative_to(cloned_path))
                        except ValueError:
                            subdir_rel = sub_skill_name

                        # 调用单个 skill 的安装流程
                        _install_single_skill(
                            source_path=skill_dir,
                            skill_name=sub_skill_name,
                            scope=args.scope,
                            is_git=True,
                            source_url=source_input,
                            source_subdir=subdir_rel,
                            commit_hash=current_hash,
                        )
                    print(f"\n✅ All {len(selected)} skill(s) installed!")
                    return  # 多 skill 安装完毕，直接返回

            else:
                # 无 SKILL.md 结构：输出 README 供 Agent/用户阅读
                print(f"   ⚠️  No SKILL.md found in this repository.")

                if analysis["readmes"]:
                    print(f"   📖 Printing README for reference...")
                    print_readme_content(analysis["readmes"][0])
                    print(f"\n💡 Tip: This repo may require manual setup.")
                    print(
                        f"   Please read the README above for installation instructions."
                    )
                    print(f"   Cloned to: {cloned_path}")
                else:
                    print(f"   ❌ No README found either.")
                    print(f"   Cloned to: {cloned_path}")

                # 询问用户是否仍要强制安装整个 repo 作为 skill
                response = (
                    input("\n⚠️  Force install the entire repo as a skill? [y/N]: ")
                    .strip()
                    .lower()
                )
                if response != "y":
                    print("\n❌ Installation cancelled. Repo is preserved at:")
                    print(f"   {cloned_path}")
                    temp_dir = None  # 不清理临时目录，保留给用户
                    sys.exit(0)

                source_path = cloned_path

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

        # 统一调用安装流程
        _install_single_skill(
            source_path=source_path,
            skill_name=skill_name,
            scope=args.scope,
            is_git=is_git,
            source_url=source_input,
        )

    finally:
        # Cleanup temp if used
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
