# Codex Project Template

面向真实代码仓库的 Codex-first 工程治理模板。它先以只读方式调查目标项目，再生成
有证据来源的 AI 约束、审批工作流、模块边界、编码规范路由、变更影响分析、验证规范
和基础 skills。对新增和实质修改的代码，它会按检测到的语言选择经过核验的行业工程
基线，同时分析目标项目已有约束和机械检查。

当前模板版本：`1.3.0`。

## 核心原则

- **先方案、后批准、再修改**：所有写操作都必须建立明确的范围合同。
- **越界即停止**：新增文件、模块、依赖、公共契约、配置或外部操作必须重新确认。
- **证据优先**：不猜测目标项目的架构、命令、语言、框架或产品规则。
- **行业基线优先**：新增和实质修改的代码使用对应语言的权威工程规范；已有规则作为
  兼容证据，强制构建、契约、安全和平台要求仍是硬边界。
- **规范持续演进**：同类人工修正达到三处或跨任务重复时，记录候选并优先转成经过
  批准的规则、formatter、linter、静态检查、模板、生成器或测试。
- **防止回归**：从变更点追踪调用方、消费者、契约、数据、配置和部署影响。
- **模块化演进**：明确模块职责和依赖方向，公共库抽取必须通过稳定性和文档门禁。
- **有界上下文**：用机器可读模块图和上下文路由限制首轮文件与字节量，只按证据扩展。
- **精准验证**：按变更路径选择有出处的检查；选择结果不等于命令执行授权。
- **软硬结合**：`AGENTS.md` 与 skills 负责上下文规则；格式化、静态检查、测试、CI、
  hooks、审批和沙箱负责可机械执行的边界。

## 安装

推荐把 `initialize-codex-project` 目录链接到用户级 skills：

```text
$HOME/.agents/skills/initialize-codex-project
    → <本仓库>/initialize-codex-project
```

Codex 支持 symlinked skill 目录。安装后，在目标 Git 仓库中开始新任务并输入：

```text
使用 $initialize-codex-project。

只读调查当前仓库并提出 Codex-first 工作流初始化方案。
识别模块、入口、公共契约、消费者、测试、构建命令和生成目录。
按文件和构建证据选择适用的语言工程规范，并报告与现有规则的冲突。
先报告证据、缺口、拟创建或合并的文件、影响、风险和验证。
在我批准精确文件清单前不要修改。
```

## 强制工作流

```text
只读调查
   ↓
方案与精确文件清单
   ↓
使用人员明确批准
   ↓
按批准范围实施
   ↓
发现越界则停止并重新批准
   ↓
$build-and-test
   ↓
$code-review
```

## 默认产物

实际文件按目标仓库证据和使用人员批准选择，不要求机械生成无用文档。完整模板包括：

```text
<target-repository>/
├── AGENTS.md
├── .agents/
│   ├── ai/
│   │   ├── project-map.json
│   │   └── verification-routes.json
│   └── skills/
│       ├── build-and-test/
│       │   ├── SKILL.md
│       │   └── scripts/select_checks.py
│       ├── code-review/SKILL.md
│       └── context-discovery/
│           ├── SKILL.md
│           └── scripts/build_context_pack.py
├── docs/
│   ├── ADR_TEMPLATE.md
│   ├── AI_CONTEXT_STRATEGY.md
│   ├── AI_PERFORMANCE_BUDGET.md
│   ├── ARCHITECTURE.md
│   ├── CHANGE_IMPACT.md
│   ├── CODEX_TEMPLATE_STATE.json
│   ├── CODEX_USAGE.md
│   ├── CODEX_WORKFLOW.md
│   ├── CODING_RULES_LOG.md
│   ├── CODING_STANDARDS.md
│   ├── LIBRARY_DOCUMENTATION_TEMPLATE.md
│   ├── MODULE_MAP.md
│   ├── SHARED_LIBRARY_STANDARD.md
│   ├── SKILLS_SPEC.md
│   ├── TASK_TEMPLATE.md
│   └── VERIFICATION.md
```

目标仓库没有权威产品或架构规范时，模板会记录清晰的 documentation gap，等待责任人
决策。编码规范会从目标语言证据选择经过核验的行业基线，但 formatter、linter、编译器、
CI、框架、兼容和项目例外仍必须从目标证据确认。

## 语言工程规范

初始化器通过只读路径元数据选择 Swift、Objective-C、Kotlin、Java、TypeScript/
JavaScript、Web Frontend、Python、Go、Rust、C 或 C++ profile。Web Frontend 覆盖
HTML/CSS、Sass/Less、JSX/TSX、Vue、Svelte、Astro 及常见前端构建标记。规则来源记录在
`initialize-codex-project/references/engineering-standards/catalog.json`，语言歧义会报告为
候选而不是强行选择。selector 不读取业务源码，不执行命令，也不修改目标仓库：

```text
python3 -B initialize-codex-project/scripts/select_language_profiles.py \
  --project-root <target-repository>
```

生成后的 `docs/CODING_STANDARDS.md` 既包含所选语言规范，也记录目标项目已有工具、
约束和冲突。行业基线指导新增及实质修改代码；冲突的工具配置和历史代码迁移需要
单独批准，不能混入普通功能变更。

当同一种人工修改或审查意见出现至少三次，或跨任务重复发生时，使用
`docs/CODING_RULES_LOG.md` 记录证据、范围、替代规则、冲突、执行方式和决策。能机械
检查的规则应优先转成工具或测试；替换规则、修改配置和批量迁移仍受审批门禁约束。

## 确定性渲染

优先让 skill 完成调查和方案确认。对于全新且无冲突的文件，可使用内置渲染器：

```text
python3 -B initialize-codex-project/scripts/render_template.py \
  --context initialize-codex-project/examples/context.example.json \
  --target <target-repository> \
  --dry-run

python3 -B initialize-codex-project/scripts/render_template.py \
  --context <approved-context.json> \
  --target <target-repository> \
  --write
```

上下文由 `values` 和可选的 `include` 组成。省略 `include` 会渲染全部模板；指定时只
渲染列出的模板源路径。必须先审查 dry-run 输出并批准完整文件清单，才能运行
`--write`。

渲染器具备以下安全性质：

- 不覆盖任何内容不同的目标文件；所有冲突在写入前统一失败。
- `.template` 后缀会被移除，模板 `skills/` 会映射到目标 `.agents/skills/`。
- 拒绝缺失、未知或畸形占位符以及不安全路径。
- 生成 `docs/CODEX_TEMPLATE_STATE.json`，记录模板版本、上下文哈希、源/目标映射和
  文件哈希，不记录上下文原文。
- 对已存在的同名规则采用“只读比较 → 聚焦合并方案 → 重新批准”，不绕过冲突保护。
- `_JSON` 结构化占位符只接受非空 JSON 对象/数组；生成后的路由文件会再次执行严格
  JSON 与 schema 校验。

## Token 与大型项目性能

模板采用“路径/符号搜索 → 模块路由 → 有界 Context Pack → 证据触发扩展”，避免默认
读取全仓库。`.agents/ai/project-map.json` 记录模块、入口、契约、消费者、测试、排除项和
预算；`$context-discovery` 的脚本只输出候选路径、原因和字节数，不输出源码内容。

`.agents/ai/verification-routes.json` 把变更路径映射到有出处的检查命令，
`select_checks.py` 只给出候选列表，并固定返回 `execution_authorized: false`。这样可以减少
无关检查和往返，但不会绕过任务授权。

本仓库的 routing benchmark 使用文件数、字节数和命令数作为可重复代理指标；它们不
等同于真实模型 token、费用或延迟。只有运行环境提供稳定遥测时才记录真实 token，并且
任何优化都不能降低审批边界、正确性、安全、兼容、消费者覆盖或验证质量。

## 公共库原则

相似代码不等于共享抽象。公共库至少需要稳定且聚焦的职责、真实独立消费者、清晰
公共 API、独立测试、消费者契约测试、版本/兼容/迁移策略以及完整使用文档。新库、
包链接、仓库引用或生产依赖始终属于需要明确批准的范围扩张。

详细规则见生成后的 `docs/SHARED_LIBRARY_STANDARD.md` 和
`docs/LIBRARY_DOCUMENTATION_TEMPLATE.md`。

## 本仓库验证

本项目不安装第三方 Python 依赖。提交前运行：

```text
python3 -B initialize-codex-project/scripts/validate_templates.py
python3 -B -m unittest discover -s tests -v
python3 -B initialize-codex-project/scripts/benchmark_routing.py
git diff --check
git status --short
```

验证覆盖模板清单、UTF-8、占位符、结构化 JSON/schema、语言 profile 目录与官方来源、
选择器歧义处理、输出路径、内部引用、skill frontmatter、规则 ID、版本、路由预算、
重复渲染稳定性、冲突拒绝和无部分写入。

## 安全边界

- initializer 默认只生成已批准的文档和 repository skills。
- 不修改目标业务源码、依赖、CI、构建配置、Git 历史或外部系统。
- 不安装工具来猜测命令，不执行未经批准的 mutating formatter。
- 不覆盖已有 `AGENTS.md`、docs 或同名 skills。
- 不把本模板项目或其他仓库的产品、架构和个性化决策带入目标项目；语言规则只来自
  根据目标证据选中的、注明权威来源的行业 profile。
- 目标项目的 CI、hooks、沙箱或命令规则只能在单独分析和批准后建立。

## 升级策略

生成的项目不会被本仓库自动修改。升级时读取目标项目中的
`docs/CODEX_TEMPLATE_STATE.json`，比较版本和文件哈希，提出逐文件合并与迁移方案，
获得批准后再更新。版本变化记录在 [CHANGELOG.md](CHANGELOG.md)。
