# Codex Project Template

通用的 Codex-first 项目初始化 Skill。它会调查目标仓库，再基于模板生成项目专属的
`AGENTS.md`、工作流、任务模板、验证规范、使用说明，以及 `build-and-test` 和
`code-review` 两个基础 skills。

## 安装

推荐把 `initialize-codex-project` 目录链接到用户级 skills：

```text
$HOME/.agents/skills/initialize-codex-project
    → <本仓库>/initialize-codex-project
```

Codex 官方支持 symlinked skill 目录。安装后，在任意目标 Git 仓库中开始新任务并输入：

```text
使用 $initialize-codex-project。

分析当前仓库并建立 Codex-first 项目工作流。
先给出调查结果和拟生成文件；确认不会覆盖现有文件后再执行。
要求：
- 先调查技术栈、目录、架构、构建、测试、格式化和 CI。
- 先报告调查结果和拟生成文件。
- 不覆盖现有 AGENTS.md、docs 或同名 skills。
- 不修改业务源码、依赖、CI 或构建配置。
- 确认后再生成。
```

## 默认产物

```text
<target-repository>/
├── AGENTS.md
├── docs/
│   ├── CODEX_WORKFLOW.md
│   ├── CODEX_USAGE.md
│   ├── TASK_TEMPLATE.md
│   ├── VERIFICATION.md
│   └── SKILLS_SPEC.md
└── .agents/
    └── skills/
        ├── build-and-test/
        │   └── SKILL.md
        └── code-review/
            └── SKILL.md
```

模板不会创建产品规范、架构规范或编码规范的虚假内容。目标仓库没有这些文档时，
`AGENTS.md` 会只引用实际存在或本次明确创建的文件。

## 安全边界

- 不修改业务源码、依赖、CI、构建配置或 Git 历史。
- 不覆盖已有 `AGENTS.md`、docs 或同名 skills；先比较并提出合并方案。
- 不猜测 build/test/lint 命令；必须从当前仓库配置或成功的只读探测中确认。
- 不把源项目的产品、语言或工具规则带入目标项目。
- 完成前运行 skill 校验、路径检查和 `git diff --check`。
