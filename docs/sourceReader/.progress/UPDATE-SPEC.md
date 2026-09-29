# sourceReader 文档库更新规范（2026-09-29 起生效）

本文件是 `docs/sourceReader/` 全部文档的**写作与定位规范**。任何更新该目录文档的工作，
先读本文件，再动手。

## 一、当前基准

| 项 | 值 |
|---|---|
| 基准提交 | `7fad4a9772`（2026-09-29 前后） |
| 上一版基准 | `cc0a679f14`（2026-09-21，共 16321 个 commit 漂移） |
| 更早基准 | `8f97ae9aec729bcbbad17da462115e1ec1398421`（2026-08-17）/ `aff5125f8edf5095aef5d3d79bbbb101c95b9413` |
| 本次漂移 | 6296 个 commit（`cc0a679f14..HEAD`） |
| 本次更新日期 | 2026-09-29 |
| 生成方式 | 源码静态分析（**未运行测试套件**，不对"测试是否通过"作声明） |

> 历史教训：上一版文档把**绝对行号**作为主要定位依据，一次上游合并后 117 处行号引用
> **100% 失效**。本版起一律使用「符号 + 偏移」记法。

## 二、定位记法（强制）

**禁止把绝对文件行号作为定位依据。**

- **函数/方法**：`文件路径` · `符号名` `+N`（`+0` = 函数定义行，`+N` = 函数体内第 N 行）
  ```
  agent/turn_facade.py · TurnFacadeMixin.run_conversation +0      （定义行）
  agent/turn_facade.py · TurnFacadeMixin.run_conversation +35~+40 （函数体内的某段）
  ```
- **类**：`agent/turn_facade.py` · `class TurnFacadeMixin` `+0`
- **模块级常量/模块变量**：`Module:tools/registry.py` · `Const:_MAX_TOOL_ERROR_CHARS`
- **调用关系**：调用方与被调用方都标，箭头区分方向
  ```
  cli.py · HermesCLI.chat ↓ agent/turn_facade.py · TurnFacadeMixin.run_conversation
  ```
- **第三方依赖**：注明版本或来源（如 `依赖：openai` / `依赖：prompt_toolkit`）
- 文档正文中**不得出现** `@1234` 这类绝对行号记法。

### 定位工具

`docs/sourceReader/.progress/sr_tools.py`（在仓库根目录执行）：

```bash
python3 docs/sourceReader/.progress/sr_tools.py locate  SYM [SYM ...]   # 全库定位符号定义
python3 docs/sourceReader/.progress/sr_tools.py outline FILE [--top]   # 文件符号骨架
python3 docs/sourceReader/.progress/sr_tools.py offset  FILE SYM       # 符号定义行号
python3 docs/sourceReader/.progress/sr_tools.py verify  DOC.md [...]   # 校验文档引用
```

计算函数内偏移：用 `offset` 拿到定义行 `L0`，目标行 `L` → 偏移 = `L - L0`。

## 三、文档格式（强制）

每篇必须包含：

1. **头部元信息块**（引用块）：
   ```
   > 层：第 N 层（层名）
   > 状态：已按 cc0a679f14 复核
   > 复核日期：2026-09-22
   > 生成日期：（保留原值）
   > 前置阅读：[...](./...)
   > 后续阅读：[...](./...)
   ```
2. **至少 1 个 Mermaid 或 ASCII 图**（流程用 flowchart、关系用 graph、时序用 sequenceDiagram）。
3. **导航尾**：`上一篇 / 总目录 / 下一篇` 三段链接。
4. 中文正文，代码/路径/符号保持原文。

## 四、内容红线

- **禁止空泛、伪造、臆测**。无法从源码证实的结论，显式写「当前源码无法确定」。
- **禁止**「同上 / 略 / 以此类推」替代核心内容。
- **禁止**第一层提前展开第四层细节。
- 每篇每个结论都要能落到真实文件+符号；改了就要能 grep 到。

## 五、本版已确认的架构级变化（直接用，不必重新侦查）

### 5.1 `AIAgent` 已改为 14 个 Mixin 组装类

`run_agent.py` · `class AIAgent` `+0` 的基类列表（顺序即 MRO）：

| Mixin | 定义文件（符号记 `+0`） |
|---|---|
| `ClientLifecycleMixin` | `agent/client_lifecycle.py` |
| `StreamDeliveryMixin` | `agent/stream_delivery.py` |
| `StatusOutputMixin` | `agent/status_output.py` |
| `ApiRequestHooksMixin` | `agent/api_request_hooks.py` |
| `ApiErrorSummaryMixin` | `agent/api_error_summary.py` |
| `InterruptControlMixin` | `agent/interrupt_control.py` |
| `TurnExplainersMixin` | `agent/turn_explainers.py` |
| `ActivityTrackingMixin` | `agent/activity_tracking.py` |
| `RateLimitCreditsMixin` | `agent/rate_limit_credits.py` |
| `SessionPersistenceMixin` | `agent/session_persistence.py` |
| `CompressionFacadeMixin` | `agent/compression_facade.py` |
| `TurnFacadeMixin` | `agent/turn_facade.py` |
| `VisionMessagePrepMixin` | `agent/vision_message_prep.py` |
| `ReasoningParamsMixin` | `agent/reasoning_params.py` |

（定义行用 `+0` 记，不再写绝对行号。要查定义行号用 `sr_tools.py offset`。）

### 5.2 消失符号 → 新位置（上一版文档全部引用错误）

| 旧文档写法 | 现状 |
|---|---|
| `run_agent.py:AIAgent.run_conversation` | → `agent/turn_facade.py` · `TurnFacadeMixin.run_conversation` |
| `run_agent.py:AIAgent.chat` | → `agent/turn_facade.py` · `TurnFacadeMixin.chat` |
| `run_agent.py:AIAgent._persist_session` | → `agent/session_persistence.py` · `SessionPersistenceMixin._persist_session` |
| `run_agent.py:AIAgent._build_system_prompt` | 符号已不存在；实现为 `agent/system_prompt.py` · `build_system_prompt` |
| `AIAgent.__init__` 本体 | 已变转发器 → `agent/agent_init.py` · `init_agent` |
| `cli.py:load_cli_config` | → `hermes_cli/cli_config_load.py` · `load_cli_config` |
| `model_tools.py:coerce_tool_args` | → `tools/arg_coercion.py` · `coerce_tool_args` |
| `hermes_state.py:SessionDB.append_message` | → `hermes_state_messages.py` 一族 |
| `hermes_state.py:SessionDB.get_messages` | → `hermes_state_messages.py` · `get_messages` |
| `gateway/run.py:run_sync` | 符号已不存在（`GatewayRunner` 仍在 `gateway/run.py`） |
| `gateway/platforms/telegram.py` 等 | → **平台适配器已插件化**，见 5.4 |

### 5.3 `hermes_state.py` 已拆为一族 29 个兄弟模块

顶层 `hermes_state_*.py` 兄弟模块（**实测 29 个**，加本体 `hermes_state.py` 共 30 个文件），
含：`hermes_state_common` `_compression` `_dbfile`
`_errors` `_fts` `_gateway` `_guard` `_health` `_holders` `_ids` `_lockguard` `_lockowners`
`_maintenance` `_messages` `_portability` `_profile_repair` `_readpool` `_registry`
`_repair` `_rewind` `_schema` `_search` `_sessions` `_telegram` `_timeline` `_titles`
`_usage` `_user_copy` `_wal`。
`hermes_state.py` 本体仍有 `class SessionDB`（组装/门面）——它同样是 **14 个 Mixin** 组装：
`SessionSessionsMixin` `SessionFtsSetupMixin` `SessionSearchMixin` `SessionSchemaMixin`
`SessionPortabilityMixin` `SessionTelegramTopicsMixin` `SessionCompressionMixin`
`SessionGatewayMixin` `SessionMaintenanceMixin` `SessionUsageMixin` `SessionTitlesMixin`
`SessionMessagesMixin` `SessionRewindMixin` `SessionProfileRepairMixin`。

**新增兄弟（2026-09-22 之前没有）**：`hermes_state_health.py`（bd945ec384
"surface corrupt state.db as one degraded session-storage state #120274"），提供
`is_structural_corruption_error`、`mark_storage_corrupt`、`note_storage_error`、
`storage_state`、`storage_corrupt_reason`、`reset_storage_state`——把 state.db 结构损坏
从「每个前端各猜一次」收拢到一处进程级 latch。

### 5.4 平台适配器已插件化

`gateway/platforms/` 只剩基础设施（`base.py` `webhook*.py` `api_server*.py` `signal*.py`
`whatsapp*.py` `weixin.py` `yuanbao*.py` 等）。
真正的平台适配器迁到 **`plugins/platforms/<平台>/`**，共 22 个目录：
`a2a` `buzz` `dingtalk` `discord` `email` `feishu` `google_chat` `homeassistant` `irc`
`line` `matrix` `mattermost` `ntfy` `photon` `raft` `simplex` `slack` `sms` `teams`
`telegram` `wecom` `whatsapp`。

### 5.5 当前规模（用于替换上一版的旧数字，HEAD `7fad4a9772` 实测）

| 模块 | 文件数 | 上一版文档写的 |
|---|---|---|
| `agent/` | 311 py | 301 |
| `tools/` | 340 py（顶层 266） | 316 py（顶层 261） |
| `hermes_cli/` | 625 py | 536 |
| `gateway/` | 175 py | 169 |
| `tui_gateway/` | 81 py | 91 |
| `cron/` | 34 py | 31 |
| `plugins/` | 241 py，18 个插件目录 | 245 py，19 个插件目录 |
| `skills/` | 58 个 SKILL.md | 58 |
| `optional-skills/` | 152 个 SKILL.md | 150 |

**变化归因**：`plugins/` 目录数 19 → 18 是**误报**——两个方向互相抵消后 net -1，实测列表在
下方；具体增减以仓库 `git log --diff-filter=AD --name-only` 为准。

### 5.6 顶层新增文件

`hermes_startup_watchdog.py`、`registration_lifecycle.py`、`toolset_distributions.py`、
`trajectory_compressor.py`、`mini_swe_runner.py`、`hermes_state_*.py`（**29 个**，含
`hermes_state_health.py`）；`hermes_state.py` 本体共 29 + 1 = 30 个文件。
（`compat_manifest.json` / `COMPAT_MANIFEST.md` **已随插件兼容层一起删除**，见 5.10。）

### 5.7 上游 `docs/` 目录已清空

上一版文档引用的 `docs/ADR.md`、`docs/observability/*`、`docs/rfcs/*`、
`docs/session-lifecycle.md`、`docs/middleware/README.md` 等 18 个文件在 HEAD 中**已不存在**。
引用这些路径的段落必须改写或删除。

**⚠ 勘误（勿重复犯错）**：`gateway/ADDING_A_PLATFORM.md` **并未消失**，真实路径是
`gateway/platforms/ADDING_A_PLATFORM.md`。上一版文档少写了 `platforms/` 一层，属**路径写错**
而非文件缺失。该文件的内容滞后也已在 2026-09-22 修正（WhatsApp 兄弟适配器示例、参考实现路径）。

**⚠ 勘误 2**：`hermes_state_*` 兄弟模块实测 **28 个**（早期草稿曾误写 36）。
`gateway/run.py` · `class GatewayRunner` 同样是 **17 个 Mixin** 组装，不是单文件类。

**⚠ 勘误 3（2026-09-22 补）**：`agent/relay_runtime.py` **不是**前端事件通道，也不是
`gateway/relay/` 的连接器中继，而是 **NVIDIA NeMo Relay**（agent 可观测性/插桩运行时，
外部包 `nemo_relay`，懒加载）。本仓库里 `relay` 一词至少三义，见 `11-并发模型与生命周期.md` §8.1。
前端通道是 JSON-RPC over stdio/WS（见 16 篇）。

**⚠ 勘误 4（2026-09-22 补）**：`cron/AGENTS.md` 与
`website/docs/developer-guide/cron-internals.md` **并不滞后**——早期的「Key Files 表过期」判断是
**误判**，两者引用的文件全部存在且正确。以后不要再基于该判断去改这两个文件。

### 5.8 上游文件抽查结论（2026-09-29 复核）

对 11 个上游 `AGENTS.md` + `website/docs/developer-guide/*.md` 做了路径校验，**真正失效的只有 2 处**
（其余为写法风格或跨仓库/运行期路径）：

| 文件 | 问题 | 修法 |
|---|---|---|
| `skills/AGENTS.md` | 指向 `references/new-skill-pr-salvage.md`，并称其在 `hermes-agent-dev` skill 里 | 该 skill 已改名 `hermes-agent-skill-authoring`，且**无** `references/` 目录；清单内容已并入其 SKILL.md 正文 → 改指 `skills/software-development/hermes-agent-skill-authoring/SKILL.md` |
| `tui_gateway/AGENTS.md` | Key surfaces 表写 `sessionPicker.tsx` | 该组件已被 `fabca0bdd8` 删除（unified Sessions overlay）→ 改为 `activeSessionSwitcher.tsx`，方法补 `session.active_list` / `session.delete` |

**已知的合法「失效」形态（不要误修）**：树状图内的相对条目（`dingtalk/adapter.py` 在
`plugins/platforms/` 树下）、`~/.hermes/config.yaml` 这类 home 路径、`HERMES_HOME/...` 这类
环境变量前缀路径、跨仓库引用（`docs/capability-trust-boundary.md` 明确标注 "connector repo"）、
示例/占位名（`tools/your_tool.py`、`test_x.py`）、库名（`discord.py`）、省略号路径
（`apps/desktop/.../x.ts`）。

### 5.9 `sr_tools.py verify` 的分桶语义（2026-09-22 修正后）

校验器只把**第一个桶**当待修项，其余三桶都**不是错误**：

| 桶 | 含义 | 处置 |
|---|---|---|
| ✗ 疑似失效路径 | 多基址都解析不到，且不属于下列任何一类 | **逐条人工判读后再修**（仍可能是合法形态，见 5.8） |
| · 说明性引用 | 该行含「不存在 / 已删除 / 已迁移」等否定词 | 正文已声明不存在，不改 |
| · 非仓库文件名 | 无 `/` 的 `*.yaml|yml|json` | `config.yaml`、`plugin.yaml` 这类运行期配置名 |
| · 裸名缩写 | 无 `/` 但仓库里存在同名文件 | 写法风格（如根 `AGENTS.md` 说 `jobs.py`），不改 |

**工具本身修过的三个缺陷（别再退回去）**：
1. 路径只按 CWD 解析 → 嵌套文档（`apps/desktop/AGENTS.md` 里的 `src/store/composer.ts`）
   全被误报。现按 `.` + 文档自身目录链多基址解析。
2. 正则会把方法名当文件名：`code_kernel.shutdown_kernels_for_delegated_child` 匹配出
   `code_kernel.sh`。现加前后 `[A-Za-z0-9_]` 边界断言（注意**不能**把 `.` 放进后视集，
   否则 `~/.hermes/config.yaml` 又匹配不到）。
3. 报告只打 basename，12 个 `AGENTS.md` 无法区分 → 现打完整路径。

### 5.10 插件兼容层已删除（2026-09-29 重大变化）

**Commit**：`a5bd246865` "Old pre-decomposition import paths are gone: plugin compat layer
removed on schedule (#126164)"，删除了以下**上一版文档大量引用**的资产：

| 消失项 | 用途 | 出现于上一版文档 |
|---|---|---|
| `COMPAT_MANIFEST.md` | 拆分清单的叙述版 | 01 / 07 / 09 / 14 / 15 |
| `compat_manifest.json` | 拆分清单的机读版（schema 1，~2087 条） | 01 / 07 / 09 / 14 / 15 |
| `scripts/check_compat_pointers.py` | CI 里的 in-tree 守卫 | 05 / 07 / 09 / 13 / 14 |
| `hermes plugins compat` 子命令 | 插件兼容报告 | 07 / 14 |
| `hermes doctor` 的 compat 分区 | 兼容性警告 | 14 |
| `plugins.allow_deprecated_imports` 配置项 | 兼容逃逸开关（代码已删） | 07 / 14 |
| 328 个 `PLUGIN-COMPAT` `__getattr__` 懒指针块 + 3 个 re-export 桩（`gateway/startup_watchdog.py`、`hermes_cli/observability/relay_runtime.py`、`tools/environments/modal_utils.py`） | 保留的旧 import 路径 | 09 |

**残留**：`hermes_cli/plugin_compat.py` 仍在，但只剩 **22 行 inert stub**（`compat_report()` 返回 `{}`、
`removal_in_effect()` 恒 `True`、`summary_lines()` 返回 `[]`），仅为兼容 `hermes update` 的老更新器
在 swap 之后仍能 lazy-import 这三个名字。该模块**没有任何生产调用点**——`grep -rn` 全库只有其
自身定义，没有其他引用。

**引用规则更新**：所有文档中把 `COMPAT_MANIFEST.md` / `compat_manifest.json` /
`scripts/check_compat_pointers.py` 当作**现存资产**的段落必须改写或删除，改为「已于 a5bd246865 删除」
的说明性引用（会被 `verify` 归到「· 说明性引用」桶，不再算失效）。相关章节：

- 14-构建部署与运维.md §八「插件兼容清单」整体改写为「已删除」。
- 07-配置体系与环境变量.md §十一改为「已删除 + 残留 stub」。
- 09-技能系统与插件架构.md 拆分章节改写为「兼容窗口已到期并删除」。
- 01 / 05 / 13 / 15 单行提法改为「已于 a5bd246865 删除」的说明性引用。

### 5.11 本轮漂移的其余结构性变化（2026-09-29 记录）

- **`hermes_state_health.py` 新增**（bd945ec384）：把 state.db 结构损坏收拢到一处进程级 latch，
  见 5.3。
- **`plugins/platforms/`** 目录数保持 22 个（与上一版一致）；`plugins/` 目录总数 18（上一版报的 19
  已过期，具体增减以 `git log --diff-filter=AD --name-only` 为准）。
- **`agent/turn_facade.py`** · `TurnFacadeMixin.run_conversation`：注释中「relay/accounting/portal」
  已明确写为「NeMo Relay」（NVIDIA NeMo 可观测性运行时），与 5.7 勘误 3 一致。
- **`hermes_cli/plugin_compat.py`** 已从「兼容指针表 + 扫描器」退化为 22 行 stub，见 5.10。
- 无新的 AIAgent / SessionDB / GatewayRunner Mixin 增减：三个组装类基类列表相对上一版**保持不变**
  （AIAgent 15 Mixin、SessionDB 14 Mixin、GatewayRunner 17 Mixin；`hermes_state_health.py` 不是
  Mixin，只是被 `hermes_state.py` 顶层 import 的工具模块）。

## 六、收尾校验（每篇写完必做）

```bash
python3 docs/sourceReader/.progress/sr_tools.py verify docs/sourceReader/<你改的篇目>.md
```

要求：失效文件路径 = 0；文档内 `@数字` 行号引用 = 0。
