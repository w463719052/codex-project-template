# Codex Project Template

为项目生成少量、可维护的 Codex 指导。默认只写四份指导文件；已有项目的规则和业务事实
从实际仓库取证，不套用其他项目的定制。

当前模板版本：`3.0.1`。

## 默认生成什么

```text
AGENTS.md                      简短入口、项目路径与必要约束
 docs/CODEX_WORKFLOW.md         范围、授权与交付流程
 docs/CODING_STANDARDS.md       适用语言规范与项目约束
 docs/VERIFICATION.md           已验证命令与使用条件
 docs/CODEX_TEMPLATE_STATE.json 自动状态清单，供需要时检查升级
```

日常直接描述任务即可。Codex 按范围读取工作流；改源码时读适用标准，验证时读相关命令。
无需填写任务表、维护路由 JSON、记录指纹或依次调用多个 skills，也不应每轮读取所有文档。

默认不生成项目地图、验证路由、项目级 skills、规则日志或任务模板。保留 L1–L4 授权边界、
已有工作保护、基于证据的命令选择与真实验证结果。指导无法替代项目已有的编译器、测试和 CI。

## 内容如何控制

这些要求由通用模板和初始化 skill 执行，不依赖后续自动学习：

- 入口只放关键路径、硬约束及阅读入口，以生成后 60 行以内为审查目标；优先引用已有说明。
- 编码规则说明适用范围及影响的决策；引用工具配置，保留必要行业基线摘要、兼容限制和
  有证据的易错约定，避免复制整篇规范。
- 每条命令关联触发改动、出处、前提、副作用及预期结果；验证矩阵说明何时扩大检查。
- 同一任务复用仍可用且未变的指导与授权；规则变化、新模块/边界、证据冲突或上下文丢失时，
  重读必要部分。不能跳过新约束，也不承诺控制客户端重复注入。

初始化完成前检查这些内容，报告实际入口行数和缺口，不要求每日打卡。仓库校验用固定的
合成占位值检查默认指导总计不超过 10,000 字节、入口不超过 60 行，防止模板无意膨胀。
真实项目的必要事实优先，不硬截断，也不把静态体积等同于 token 或质量收益。

通用模板定义行为，初始化采集项目事实，后续根据证据和授权调整；没有后台学习、未经确认
的偏好持久化或从项目自动回写通用模板。

## 安装与初始化

将 `initialize-codex-project` 链接到用户级 skills（已有同名目录时先检查，不要覆盖）：

```sh
ln -s /absolute/path/codex-project-template/initialize-codex-project ~/.codex/skills/initialize-codex-project
```

在目标项目中调用：

```text
$initialize-codex-project 根据实际项目初始化轻量指导，先给出文件清单。
```

初始化会检查已有指导、相关源码/构建证据和工作区状态，只收集所选产物需要的字段。
语言规范来自经过核验的行业基线，并保留目标的构建、兼容、安全、隐私和公共契约约束。
不明确的事实记录为文档缺口，不猜测命令或复制其他项目的偏好。

## 渲染与配置

[示例上下文](initialize-codex-project/examples/context.example.json)只展示轻量默认所需字段。
替换为实际项目证据后先 dry-run，审查并批准完整输出清单，再写入：

```sh
python3 -B initialize-codex-project/scripts/render_template.py --context <context.json> --target <target-repository> --dry-run
python3 -B initialize-codex-project/scripts/render_template.py --context <context.json> --target <target-repository> --write
```

| 选择 | 生成模板文件数（另加一个状态清单） | 适用情况 |
| --- | ---: | --- |
| 省略 `preset` 或 `minimal` | 4 | 普通项目默认 |
| 显式 `core` | 17 | 需要维护模块/验证路由及三个项目级 skills |
| 显式 `full` | 24 | 所有架构、共享库等扩展均确有需要 |
| `include` | 按清单 | 精确选择，必须满足引用和脚本依赖 |

`preset` 与 `include` 互斥，不需要新增开关。`values` 只需提供所选模板的占位符；仍接受
旧上下文中已知但未使用的值。新增项目特定规则由目标项目自行维护。

**3.0.0 兼容变化：省略 preset 不再生成 core；minimal 也由 13 份缩减为 4 份。**
需要原 core 文件集合的调用方请显式指定 `"preset": "core"`。core/full 的文件集合保留，
共用指导文本已精简。已有目标文件不会自动删除、覆盖或迁移。

渲染器验证实际 JSON schema、占位符、必需引用与脚本依赖；缺失依赖会拒绝生成。
条件使用的扩展引用以 `<!-- optional-reference: docs/FILE.md -->` 等标记声明，不能用来
隐藏实际必需依赖。源文件 `.template` 后缀被移除；`skills/` 输出到 `.agents/skills/`。

同名非一致内容会阻止写入。安全写入使用 POSIX 目录句柄、拒绝符号链接和独占创建；失败时
只回滚本次创建且身份未变的对象，清理不完整会报错。它不是文件系统事务，不承诺抵御
进程强杀或任意并发重命名。状态清单保存版本与哈希，不保存上下文原文。

## 授权与任务记录

L1 的明确实施请求授权已声明的局部范围；L2 需要一次目录边界方案批准；L3/L4 需要精确
方案批准，L4 另需回滚与运行影响证据。超出批准边界时重新确认。完整定义在生成的工作流中。
同一范围内有效的检查授权持续有效，不重复索取。

范围、影响和结果默认在对话中说明。三次有证据的重复选择可触发规则建议，确认后才记录；
不自动建立偏好档案、任务日志或扩展配置。

## 按需扩展

显式选择 core/full 时，才生成以下维护能力：

- `.agents/ai/project-map.json`：模块、路径、契约、预算及发现路由。
- `.agents/ai/verification-routes.json`：有证据的验证命令及路径匹配。
- `.agents/skills/`：context-discovery、build-and-test、code-review 及配套脚本。
- 使用说明、任务输入模板、影响分析表和规则日志。

full 另含架构、ADR、模块地图、共享库规范、性能预算及 skill 设计指导。
精确 include 必须同时选择所需依赖。没有地图时直接按任务路径、调用者和测试做有界搜索；
没有验证路由时直接从验证文档选择命令。安装扩展不等于每个任务都要使用。

路由优先处理明确文件/模块提示，报告遗漏；泛化匹配涉及多个模块时返回 `scope_required`。
命令选择固定返回 `execution_authorized: false`，不能替代执行授权。文件数与字节数是
静态上下文指标，尚无真实模型评测证明某个 preset 普遍更省 token 或更准确。

语言范围不明确时，可使用只读选择器；`--scope` 可重复，`--role` 为显式角色标签：

```sh
python3 -B initialize-codex-project/scripts/select_language_profiles.py --project-root <target-repository> --scope <relative-module> --role application
```

## 需要维护或评测时

以下工具不属于日常任务的必读或必跑流程。

**证据审计：** 模块/命令可选 `provenance`，必填相对 `path`，可选 `sha256`、`verified_at`
（YYYY-MM-DD）、`scope`、`environment`、`prerequisites`（字符串数组）。旧 schema 1 和
字符串 `evidence` 保持兼容；不要求补齐指纹。安装相应扩展后，在目标项目运行：

```sh
python3 -B .agents/skills/context-discovery/scripts/audit_evidence.py --project-root .
```

可重复传入 `--metadata <相对JSON路径>`。current/stale/missing/unverified 分别表示字节匹配、
变化、缺失和缺少指纹。退出码 0 无 stale/missing，1 有 stale/missing，2 输入/读取错误。
它不执行命令、不更新元数据；哈希匹配不证明命令有效。

**升级报告：** 只读比较初始化基线与当前目标，可加入已核实的新上下文比较候选输出：

```sh
python3 -B initialize-codex-project/scripts/report_upgrade.py --target <target-repository>
python3 -B initialize-codex-project/scripts/report_upgrade.py --target <target-repository> --context <verified-context.json>
```

状态包括 unchanged、target-modified、template-changed、both-changed、missing、new、
already-current、unmanaged-conflict、not-selected。not-selected 不代表删除。
退出码 0 为报告成功，2 为输入/读取错误；不会自动合并、刷新哈希或写入目标。
缺少旧内容时不能仅靠哈希声称安全三方合并。

**真实评测：** 见 [A/B 协议](initialize-codex-project/references/ab-study-protocol.md)。
使用独立配对研究比较 baseline/minimal 与 baseline/core，报告各指标有效样本数。
合成样例只验证分析器，不代表实测效果；缺失 token 保持缺失，不启动模型会话。

## 本仓库验证与支持环境

Python 3.12+，无需第三方依赖。安全写入要求 macOS/Linux POSIX 目录句柄与 `O_NOFOLLOW`；
不支持 Windows 写入。CI 配置覆盖 Ubuntu 24.04/macOS 14 和 Python 3.12/3.14；远程是否通过
以实际运行记录为准。

```sh
python3 -B initialize-codex-project/scripts/validate_templates.py
python3 -B -m unittest discover -s tests -v
python3 -B initialize-codex-project/scripts/benchmark_routing.py
python3 -B initialize-codex-project/scripts/analyze_ab_study.py --input initialize-codex-project/benchmarks/ab-study.example.json
git diff --check
git status --short
```

变更记录见 [CHANGELOG.md](CHANGELOG.md)。
