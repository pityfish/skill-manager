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

*   **统一归集**: 无论来源是 npm 还是 git，所有技能都住在同一个家 (`~/.agents/skills/`)。
*   **一次安装，处处可用**: 自动检测并同步到 Antigravity, Claude, Gemini, Cursor 等所有平台。
*   **智能维护**: 自动区分技能来源，提供正确的更新方式 (`npx` vs `git`)。


## ⚡️ 你能管理什么？

无论技能来自哪里，都可以通过一套机制统一管理：

*   **社区技能 (npx)**: 安装 `browser-skill` 让 Agent 获得联网搜索能力。
*   **私有技能 (Git)**: 克隆公司的 `internal-api-skill` 让 Agent 安全操作内网数据。
*   **本地脚本 (Local)**: 直接链接你写的 Python/Node.js 脚本，快速测试新能力。

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
*   安装工具: 运行 `npx skills add <包名> -g -y`

### 👤 For Humans (管理模式)

**1. 安装新技能 (从社区)**
```bash
npx skills add browser-skill -g -y
```

**2. 安装新技能 (从 Git)**
```bash
python3 scripts/install_skill.py https://github.com/user/awesome-tool.git
```

**3. 同步与更新**
```bash
python3 scripts/update_skills.py
```

**4. 查看 Agent 当前能做什么**
```bash
python3 scripts/list_synced.py
```

## 🔌 支持的智能体

| 智能体 | 状态 | 路径 |
| :--- | :--- | :--- |
| **Claude Code** | ✅ 自动同步 | `~/.claude/skills` |
| **Google Antigravity** | ✅ 自动同步 | `~/.gemini/antigravity/skills` |
| **Gemini CLI** | ✅ 自动同步 | `~/.gemini/skills` |
| **Cursor** | ✅ 自动同步 | `~/.cursor/skills` |
| **GitHub Copilot** | ✅ 自动同步 | `~/.copilot/skills` |
| **OpenAI Codex** | ✅ 自动同步 | `~/.codex/skills` |

## ❓ 常见问题

**Q: Agent 说它找不到我在用的工具。**
A: 确保安装时加了 `-g` (全局模式)，或者运行 `python3 scripts/list_synced.py` 检查一下同步状态。

**Q: 怎么卸载技能？**
A: `python3 scripts/uninstall_skill.py <skill-name>`
