# Skill Manager (统一技能管理工具)

**Skill Manager** 是一个强大的 AI Agent 技能管理工具，旨在统一管理来自不同来源的技能，并将其自动同步到你本地安装的各种 AI 辅助工具中（如 Claude Code, Gemini CLI, Cursor 等）。

它解决了 AI 技能分散的问题，将 `npx skills` (skills.sh 生态) 和 Git/本地技能统一存储在 `~/.agents/skills/`，并提供了一套完整的生命周期管理脚本。

## ✨ 主要特性

*   **🛡️ 统一仓库**: 所有技能集中存储在 `~/.agents/skills/`，井井有条。
*   **🌍 多源支持**:
    *   📦 **skills.sh 生态**: 完美兼容 `npx skills` 安装的技能。
    *   🔗 **Git 仓库**: 支持直接从 GitHub 等 Git URL 安装。
    *   📁 **本地开发**: 支持安装本地开发的技能目录。
*   **🔄 自动同步**: 智能检测本地安装的 AI 平台（如 Claude, Gemini, Cursor），并通过软链接自动同步技能，一次安装，处处可用。
*   **🛠️ 全生命周期管理**: 提供安装、查询、更新、卸载的全套 Python 脚本。
*   **🧠 智能识别**: 自动识别技能的安装来源，并调用正确的更新/卸载逻辑（例如 `git pull` vs `npx skills update`）。

## 🚀 支持的 AI 平台

工具会自动检测以下平台并进行同步：

*   Claude Code (`~/.claude/skills`)
*   GitHub Copilot (`~/.copilot/skills`)
*   Google Antigravity (`~/.gemini/antigravity/skills`)
*   Cursor (`~/.cursor/skills`)
*   OpenCode (`~/.config/opencode/skill`)
*   OpenAI Codex (`~/.codex/skills`)
*   Gemini CLI (`~/.gemini/skills`)
*   Windsurf (`~/.codeium/windsurf/skills`)
*   Qwen Code (`~/.qwen/skills`)
*   Qoder (`~/.qoder/skills`)

## 📦 安装与配置

将此仓库克隆到你的本地环境（建议放在 `~/.agents/skills/` 下，或者任意你方便管理的地方）：

```bash
git clone https://github.com/your-username/skill-manager.git ~/.agents/skills/skill-manager
```

确保脚本具有执行权限：

```bash
chmod +x ~/.agents/skills/skill-manager/scripts/*.py
```

## 📖 使用指南

### 1. 查看已安装技能

查看所有技能及其来源、同步状态：

```bash
python3 scripts/list_synced.py
```

**输出示例**:
> 📦 find-skills [npx skills] - ✅ Synced
> 🔗 my-custom-skill [Git] - ⬇️ 2 commits behind

### 2. 安装新技能

支持从 Git URL 或本地路径安装，并自动询问要同步到哪些平台。

```bash
# 从 Git URL 安装 (全局)
python3 scripts/install_skill.py https://github.com/user/awesome-skill.git

# 安装本地目录
python3 scripts/install_skill.py ./my-local-skill/

# 安装到当前项目 (Local Scope)
python3 scripts/install_skill.py ./my-skill/ --local
```

### 3. 更新技能

自动检测技能来源并更新。

```bash
# 交互式更新 (推荐)
python3 scripts/update_skills.py

# 更新所有 Git 来源的技能
python3 scripts/update_skills.py --all

# 更新特定技能
python3 scripts/update_skills.py my-skill
```

### 4. 卸载技能

智能卸载，同时移除中心仓库和所有平台的软链接。

```bash
python3 scripts/uninstall_skill.py <skill-name>
```

如果是 `npx` 安装的技能，会提示优先使用 `npx skills remove`。

## 📂 目录结构

```text
~/.agents/skills/                 ← 中心仓库 (Central Repository)
    ├── skill-manager/            ← 本工具
    ├── my-skill/                 ← 用户安装的技能
    ├── find-skills/              ← npx 安装的技能
    └── ...

~/.claude/skills/                 ← 平台目录
    └── my-skill -> ~/.agents/skills/my-skill  ← 自动创建的软链接
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个工具！
