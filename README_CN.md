# ⚡️ Agent Skill Manager (智能体技能中心)

[🇺🇸 English](./README.md) | [🇨🇳 中文](./README_CN.md)

> **AI 智能体技能的统一管理器**
>
> 将 `skills.sh` 生态与自定义 Git 技能集中管理，并同步到你所有的 AI 助手。

---

## 🤖 这是什么？

这是一个 **统一技能管理工具 (Unified Skill Manager)**，它将两个平行的技能世界整合在一起：

1.  **skills.sh 生态**: 通过 `npx skills` 安装的开源社区技能。
2.  **手动/Git 技能**: 你通过 Git 或本地路径手动安装的私有技能。

它将**所有**能力统一收敛到 `~/.agents/skills/` 目录，并自动分发同步到 **Claude**, **Gemini**, **Cursor** 等所有工具中。

## 🚀 核心价值

*   **统一归集**: 无论来源是 npm 还是 git，所有技能都住在同一个家。
    *   **全局 (Global)**: `~/.agents/skills/` (所有项目共用)
    *   **项目 (Project)**: `./.agents/skills/` (仅限当前项目)
*   **一次安装，处处可用**: 自动同步到 Claude, Gemini, Cursor, Trae, Replit 等所有平台。


## ⚡️ 你能管理什么？

无论技能来自哪里，都可以通过一套机制统一管理：

*   **社区技能 (npx)**: 安装 `browser-skill` 让 Agent 获得联网搜索能力。
*   **私有技能 (Git)**: 克隆公司的 `internal-api-skill` 让 Agent 安全操作内网数据。
*   **本地脚本 (Local)**: 直接链接你写的 Python/Node.js 脚本，快速测试新能力。

## ⚠️ 环境要求 (Prerequisites)

在安装之前，请确保你的环境满足以下要求：

- **操作系统**: macOS 或 Linux (Windows/WSL 支持尚处于实验阶段)。
- **Python**: 3.9 或更高版本 (使用了 `pathlib` 的高级特性)。
- **Node.js**: 必需，用于支持 `skills.sh` 生态及 `npx` 命令。
- **Git**: 必需，用于从代码仓库获取技能。

## 📦 安装 (Installation)

一行命令完成桥接。

```bash
git clone https://github.com/your-username/skill-manager.git ~/.agents/skills/skill-manager && chmod +x ~/.agents/skills/skill-manager/scripts/*.py
```

## 📖 使用指南

### 🗣️ 触发指令示例 (Natural Language)

作为一个 Agent Skill，你可以直接用自然语言指挥你的 Agent：

*   "帮我找一个处理 PDF 的 skill"
*   "安装 `browser-skill`，要全局安装"
*   "列出我现在安装了哪些 skill"
*   "同步一下我的 skills"
*   "我想管理日历，有没有现成的工具？"

### 🤖 For Agents (自动模式)

如果你是正在阅读此文档的 AI Agent：**你有新的技能可用了。**
请查阅 `SKILL.md` 获取详细的触发方式。

*   查找工具: 运行 `npx skills find <意图>`
*   安装/管理: 请查阅 `SKILL.md` 获取完整的非交互 CLI 命令。

### 👤 For Humans (管理模式)

**1. 安装新技能 (推荐统一命令)**
脚本自动处理 Registry 名称、Git 链接及本地路径。
```bash
# 交互模式 (TUI 提示选择 scope 和 agents):
python3 scripts/install_skill.py <技能名或链接>

# 非交互模式 (适用于 Agent 或自动化脚本):
python3 scripts/install_skill.py <技能名或链接> --scope global --agents all --yes
```

> 💡 **智能 Git 安装**：从 GitHub URL 安装时，脚本会自动分析 repo 结构。如果 repo 包含多个子目录 skill，使用 `--skills all` 或 `--skills name1,name2` 来选择；如果找不到 `SKILL.md`，会打印 README 供参考。

**3. 同步与更新**
```bash
# 非交互一键更新 (推荐 Agent 使用):
python3 scripts/update_skills.py --all --scope global

# 交互式更新 (TUI 按需勾选):
python3 scripts/update_skills.py

# 更新指定技能:
python3 scripts/update_skills.py <技能名称>
```

**4. 查看 Agent 当前能做什么**
```bash
# 精简模式 (紧凑输出，适合 Agent):
python3 scripts/list_skills.py --brief

# 完整详情:
python3 scripts/list_skills.py
```

**5. 彻底卸载**
```bash
# 非交互 (从所有位置移除):
python3 scripts/uninstall_skill.py <技能名称> --scope global --all-locations

# 交互模式 (TUI 选择):
python3 scripts/uninstall_skill.py
```

## 🔌 支持的智能体

| Platform | Global Path | Project Path |
| :--- | :--- | :--- |
| **AdaL** | `~/.adal/skills` | `.adal/skills` |
| **Amp** | `~/.config/agents/skills` | `.agents/skills` |
| **Antigravity** | `~/.gemini/antigravity/skills` | `.agent/skills` |
| **Augment** | `~/.augment/skills` | `.augment/skills` |
| **Claude Code** | `~/.claude/skills` | `.claude/skills` |
| **Cline** | `~/.agents/skills` | `.agents/skills` |
| **CodeBuddy** | `~/.codebuddy/skills` | `.codebuddy/skills` |
| **Codex** | `~/.codex/skills` | `.agents/skills` |
| **Command Code** | `~/.commandcode/skills` | `.commandcode/skills` |
| **Continue** | `~/.continue/skills` | `.continue/skills` |
| **Cortex Code** | `~/.snowflake/cortex/skills` | `.cortex/skills` |
| **Crush** | `~/.config/crush/skills` | `.crush/skills` |
| **Cursor** | `~/.cursor/skills` | `.agents/skills` |
| **Droid** | `~/.factory/skills` | `.factory/skills` |
| **Gemini CLI** | `~/.gemini/skills` | `.agents/skills` |
| **GitHub Copilot** | `~/.copilot/skills` | `.agents/skills` |
| **Goose** | `~/.config/goose/skills` | `.goose/skills` |
| **iFlow CLI** | `~/.iflow/skills` | `.iflow/skills` |
| **Junie** | `~/.junie/skills` | `.junie/skills` |
| **Kilo Code** | `~/.kilocode/skills` | `.kilocode/skills` |
| **Kimi Code CLI** | `~/.config/agents/skills` | `.agents/skills` |
| **Kiro CLI** | `~/.kiro/skills` | `.kiro/skills` |
| **Kode** | `~/.kode/skills` | `.kode/skills` |
| **MCPJam** | `~/.mcpjam/skills` | `.mcpjam/skills` |
| **Mistral Vibe** | `~/.vibe/skills` | `.vibe/skills` |
| **Mux** | `~/.mux/skills` | `.mux/skills` |
| **Neovate** | `~/.neovate/skills` | `.neovate/skills` |
| **OpenClaw** | `~/.openclaw/skills` | `skills` |
| **OpenCode** | `~/.config/opencode/skills` | `.agents/skills` |
| **OpenHands** | `~/.openhands/skills` | `.openhands/skills` |
| **Pi** | `~/.pi/agent/skills` | `.pi/skills` |
| **Pochi** | `~/.pochi/skills` | `.pochi/skills` |
| **Qoder** | `~/.qoder/skills` | `.qoder/skills` |
| **Qwen Code** | `~/.qwen/skills` | `.qwen/skills` |
| **Replit** | `~/.config/agents/skills` | `.agents/skills` |
| **Roo Code** | `~/.roo/skills` | `.roo/skills` |
| **Trae** | `~/.trae/skills` | `.trae/skills` |
| **Trae CN** | `~/.trae-cn/skills` | `.trae/skills` |
| **Windsurf** | `~/.codeium/windsurf/skills` | `.windsurf/skills` |
| **Zencoder** | `~/.zencoder/skills` | `.zencoder/skills` |

## ❓ 常见问题

**Q: Agent 说它找不到我在用的工具。**
A: 运行 `python3 scripts/list_skills.py --brief` 检查当前状态，确认技能已同步到你使用的 Agent 平台。

**Q: 怎么卸载技能？**
A: `python3 scripts/uninstall_skill.py <skill-name> --scope global --all-locations`。如果它是 Registry 技能，脚本会自动触发 `npx skills remove`。
