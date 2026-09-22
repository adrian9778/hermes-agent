# sourceReader 文档库更新规范（2026-09-22 起生效）

本文件是 `docs/sourceReader/` 全部文档的**写作与定位规范**。任何更新该目录文档的工作，
先读本文件，再动手。

## 一、当前基准

| 项 | 值 |
|---|---|
| 基准提交 | `cc0a679f14`（2026-09-21） |
| 上一版基准 | `8f97ae9aec729bcbbad17da462115e1ec1398421`（2026-08-17）/ `aff5125f8edf5095aef5d3d79bbbb101c95b9413` |
| 中间漂移 | 16321 个 commit |
| 本次更新日期 | 2026-09-22 |
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

### 5.3 `hermes_state.py` 已拆为一族 28 个兄弟模块

顶层 `hermes_state_*.py` 兄弟模块（**实测 28 个**，加本体 `hermes_state.py` 共 29 个文件），含：`hermes_state_common` `_compression` `_dbfile`
`_errors` `_fts` `_gateway` `_guard` `_holders` `_ids` `_lockguard` `_lockowners`
`_maintenance` `_messages` `_portability` `_profile_repair` `_readpool` `_registry`
`_repair` `_rewind` `_schema` `_search` `_sessions` `_telegram` `_timeline` `_titles`
`_usage` `_user_copy` `_wal`。
`hermes_state.py` 本体仍有 `class SessionDB`（组装/门面）——它同样是 **14 个 Mixin** 组装：
`SessionSessionsMixin` `SessionFtsSetupMixin` `SessionSearchMixin` `SessionSchemaMixin`
`SessionPortabilityMixin` `SessionTelegramTopicsMixin` `SessionCompressionMixin`
`SessionGatewayMixin` `SessionMaintenanceMixin` `SessionUsageMixin` `SessionTitlesMixin`
`SessionMessagesMixin` `SessionRewindMixin` `SessionProfileRepairMixin`。

### 5.4 平台适配器已插件化

`gateway/platforms/` 只剩基础设施（`base.py` `webhook*.py` `api_server*.py` `signal*.py`
`whatsapp*.py` `weixin.py` `yuanbao*.py` 等）。
真正的平台适配器迁到 **`plugins/platforms/<平台>/`**，共 22 个目录：
`a2a` `buzz` `dingtalk` `discord` `email` `feishu` `google_chat` `homeassistant` `irc`
`line` `matrix` `mattermost` `ntfy` `photon` `raft` `simplex` `slack` `sms` `teams`
`telegram` `wecom` `whatsapp`。

### 5.5 当前规模（用于替换上一版的旧数字）

| 模块 | 文件数 | 上一版文档写的 |
|---|---|---|
| `agent/` | 301 py | 195 |
| `tools/` | 316 py（顶层 261） | 121 |
| `hermes_cli/` | 536 py | 287 |
| `gateway/` | 169 py | 93 |
| `tui_gateway/` | 91 py | — |
| `cron/` | 31 py | 13 |
| `plugins/` | 245 py，19 个插件目录 | — |
| `skills/` | 58 个 SKILL.md | — |
| `optional-skills/` | 150 个 SKILL.md | — |

### 5.6 顶层新增文件

`hermes_startup_watchdog.py`、`registration_lifecycle.py`、`toolset_distributions.py`、
`trajectory_compressor.py`、`mini_swe_runner.py`、`compat_manifest.json`、
`COMPAT_MANIFEST.md`、`hermes_state_*.py`（28 个）。

### 5.7 上游 `docs/` 目录已清空

上一版文档引用的 `docs/ADR.md`、`docs/observability/*`、`docs/rfcs/*`、
`docs/session-lifecycle.md`、`docs/middleware/README.md` 等 18 个文件在 HEAD 中**已不存在**。
引用这些路径的段落必须改写或删除。

**⚠ 勘误（勿重复犯错）**：`gateway/ADDING_A_PLATFORM.md` **并未消失**，真实路径是
`gateway/platforms/ADDING_A_PLATFORM.md`。上一版文档少写了 `platforms/` 一层，属**路径写错**
而非文件缺失。但该文件内容本身已滞后（仍描述核心目录下的 telegram/discord/whatsapp 模块，
而它们已迁到 `plugins/platforms/`），引用它时应加警示。

**⚠ 勘误 2**：`hermes_state_*` 兄弟模块实测 **28 个**（早期草稿曾误写 36）。
`gateway/run.py` · `class GatewayRunner` 同样是 **17 个 Mixin** 组装，不是单文件类。

## 六、收尾校验（每篇写完必做）

```bash
python3 docs/sourceReader/.progress/sr_tools.py verify docs/sourceReader/<你改的篇目>.md
```

要求：失效文件路径 = 0；文档内 `@数字` 行号引用 = 0。
