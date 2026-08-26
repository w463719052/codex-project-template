# Codex Project Template

面向真实代码仓库的 Codex-first 工程治理模板。它先以只读方式调查目标项目，再生成
有证据来源的 AI 约束、审批工作流、模块边界、编码规范路由、变更影响分析、验证规范
和基础 skills。对新增和实质修改的代码，它会按检测到的语言选择经过核验的行业工程
基线，同时分析目标项目已有约束和机械检查。

当前模板版本：`2.0.0`。

## 核心原则

- **按风险授权**：L1 直接声明后执行，L2 一次批准目录边界，L3/L4 批准精确计划。
- **按等级控制越界**：L1 范围失效即升级，L2 离开批准目录即停止，保护边界始终重批。
- **证据优先**：不猜测目标项目的架构、命令、语言、框架或产品规则。
- **行业基线优先**：新增和实质修改的代码使用对应语言的权威工程规范；已有规则作为
  兼容证据，强制构建、契约、安全和平台要求仍是硬边界。
- **规范持续演进**：同类人工修正达到三处或跨任务重复时，记录候选并优先转成经过
  批准的规则、formatter、linter、静态检查、模板、生成器或测试。
- **习惯驱动建议**：同类明确使用行为出现至少三次时提醒可调整的规则，经使用者确认
  后再记录和同步；不从沉默推断偏好，也不静默削弱安全与验证边界。
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
任务分级与只读调查
   ↓
L1 声明 / L2 目录方案 / L3-L4 精确方案
   ↓
匹配等级的授权
   ↓
按批准范围实施
   ↓
发现越界则停止并重新批准
   ↓
$build-and-test
   ↓
$code-review
```

## 默认核心产物

省略选择参数时使用 `core` preset，只生成日常 AI 编码所需的核心文件：

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
│   ├── AI_CONTEXT_STRATEGY.md
│   ├── CHANGE_IMPACT.md
│   ├── CODEX_TEMPLATE_STATE.json
│   ├── CODEX_USAGE.md
│   ├── CODEX_WORKFLOW.md
│   ├── CODING_RULES_LOG.md
│   ├── CODING_STANDARDS.md
│   ├── TASK_TEMPLATE.md
│   └── VERIFICATION.md
```

架构、模块图、ADR、共享库、性能预算和 skill 设计文档是可选产物，只在目标证据和
批准范围需要时通过精确 `include` 或 `preset: "full"` 生成。状态清单记录最终解析后的
源文件集合，便于安全升级。

## L1-L4 授权等级

- **L1**：单模块、精确文件已知、保持公共契约/依赖/配置/数据/安全和外部状态不变。
  使用者明确要求实现、修复或修改即构成授权；AI 先简述范围和检查，然后直接执行。
- **L2**：模块内功能或调试，文件可能在已知目录内变化。使用者一次批准目录边界后，
  不因同目录新增文件重复确认。
- **L3**：跨模块、兼容、并发、数据流或公共契约敏感变更，批准精确文件和影响方案。
- **L4**：架构、安全隐私、迁移、破坏性/外部操作或高成本失败任务，保留完整影响、
  回滚和所有者证据门禁。

判断不确定时使用更高等级。依赖、构建/CI/配置、公共 API/schema、外部写入和破坏性
操作不会因为任务看起来很小而降为 L1/L2。

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

上下文由 `values`、可选 `preset` 和可选 `include` 组成。默认或
`preset: "core"` 渲染核心文件；`preset: "full"` 渲染完整模板；`include` 精确渲染列出的
模板源路径。`preset` 与 `include` 互斥。必须先审查 dry-run 输出并批准完整文件清单，
才能运行 `--write`。

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

对于真实效果，使用配对 A/B 记录比较同一任务、同一基础 revision、相同模型配置、
环境和验收检查下的两个工作流。分析器比较首次通过率、使用者往返、耗时、可用 token、
范围越界和 review 缺陷；缺失 token 保持缺失，不按零计算：

```text
python3 -B initialize-codex-project/scripts/analyze_ab_study.py \
  --input <real-study.json>
```

仓库中的 example 只验证分析器，不构成性能证据，也不会自动启动模型会话。

## 使用习惯与规则优化

生成的 `docs/CODING_RULES_LOG.md` 同时记录编码和工作流规则候选。当相同的明确操作、
纠正或批准模式有至少三条可引用证据时，AI 会在交付中提醒可调整规则，并列出证据、
收益、风险和需要同步的文件。使用者确认前不会记录行为或修改规则；拒绝项可记录重新
考虑条件，避免反复提醒。沉默、缺少证据或一次性选择都不能被当作长期偏好。

## 公共库原则

相似代码不等于共享抽象。公共库至少需要稳定且聚焦的职责、真实独立消费者、清晰
公共 API、独立测试、消费者契约测试、版本/兼容/迁移策略以及完整使用文档。新库、
包链接、仓库引用或生产依赖始终属于需要明确批准的范围扩张。

若目标证据需要并选择了可选共享库产物，详细规则见生成后的
`docs/SHARED_LIBRARY_STANDARD.md` 和 `docs/LIBRARY_DOCUMENTATION_TEMPLATE.md`。

## 本仓库验证

本项目不安装第三方 Python 依赖。提交前运行：

```text
python3 -B initialize-codex-project/scripts/validate_templates.py
python3 -B -m unittest discover -s tests -v
python3 -B initialize-codex-project/scripts/benchmark_routing.py
python3 -B initialize-codex-project/scripts/analyze_ab_study.py \
  --input initialize-codex-project/benchmarks/ab-study.example.json
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
