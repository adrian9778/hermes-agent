# sourceReader 文档库更新规范（2026-09-22 起生效；2026-10-05 二次刷新）

本文件是 `docs/sourceReader/` 全部文档的**写作与定位规范**。任何更新该目录文档的工作，
先读本文件，再动手。

## 一、当前基准

| 项 | 值 |
|---|---|
| 基准提交 | `e1fdf003a6`（2026-10-05） |
| 上一版基准 | `cc0a679f14`（2026-09-21） |
| 中间漂移 | 9098 个 commit / 10106 个改动文件 |
| 本次更新日期 | 2026-10-05 |
| 生成方式 | 源码静态分析（**未运行测试套件**，不对"测试是否通过"作声明） |

> **文档库的存放位置**：本库**不在 `main` 上**。`main` 的 `docs/` 已被上游清空（只剩
> `.DS_Store`）。本库此前一直提交在侧分支 `origin/bot/js-autofix`（最后提交 `f39bcec2d0`，
> 2026-09-22 14:48）。2026-10-05 从该分支恢复后在工作区增量刷新，**未提交**（老板 2026-10-05 定：
> 留在工作区，避免与上游 NousResearch/hermes-agent 的 pull 反复冲突）。
> 恢复命令：`git checkout origin/bot/js-autofix -- docs/sourceReader`

> 历史教训：上一版文档把**绝对行号**作为主要定位依据，一次上游合并后 117 处行号引用
> **100% 失效**。本版起一律使用「符号 + 偏移」记法。
> **该记法在 9098 commit 漂移后依然成立**——本次实测行号失效 0 处、路径失效仅 10 处。

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

> ⚠️ **本表是 2026-09-21 的快照，已被 §7.5 取代。** 引用当前数字一律用 §7.5；
> 本表只在需要「上一版文档写的是什么」时参考。

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
而非文件缺失。其内容滞后（描述核心目录下的 telegram/discord/whatsapp）已于 2026-09-22 修正。

**⚠ 勘误 2**：`hermes_state_*` 兄弟模块 2026-09-21 实测 **28 个**（早期草稿曾误写 36），
**2026-10-05 为 32 个**。`gateway/run.py` · `class GatewayRunner` 是 **17 个 Mixin** 组装，
不是单文件类。

**⚠ 勘误 3**：`agent/relay_runtime.py` **不是**前端事件通道，也不是 `gateway/relay/` 的连接器中继，
而是 **NVIDIA NeMo Relay**（agent 可观测性/插桩运行时，外部包 `nemo_relay` 懒加载）。
本仓库 `relay` 一词至少三义，见 `11-并发模型与生命周期.md` §8.1。前端通道是 JSON-RPC over stdio/WS（16 篇）。

**⚠ 勘误 4**：`cron/AGENTS.md` 与 `website/docs/developer-guide/cron-internals.md` **并不滞后**——
"Key Files 表过期"是误判，两者引用的文件全部存在且正确。不要再基于该判断去改这两个文件。

### 5.8 上游文件抽查结论（2026-09-22）

对 11 个上游 `AGENTS.md` + `website/docs/developer-guide/*.md` 做路径校验，**真正失效的只有 2 处**
（其余为写法风格或跨仓库/运行期路径）：

| 文件 | 问题 | 修法 |
|---|---|---|
| `skills/AGENTS.md` | 指向 `references/new-skill-pr-salvage.md`，称其在 `hermes-agent-dev` skill 里 | 该 skill 已改名 `hermes-agent-skill-authoring` 且**无** `references/` 目录；清单已并入其 SKILL.md → 改指 `skills/software-development/hermes-agent-skill-authoring/SKILL.md` |
| `tui_gateway/AGENTS.md` | Key surfaces 表写 `sessionPicker.tsx` | 已被 `fabca0bdd8` 删除（unified Sessions overlay）→ 改为 `activeSessionSwitcher.tsx`，方法补 `session.active_list` / `session.delete` |

同批还修了 `apps/desktop/AGENTS.md`（`store/*.ts` 缺 `src/`、`main.ts` → `electron/main.ts`）、
`gateway/platforms/ADDING_A_PLATFORM.md`（WhatsApp 兄弟适配器路径）、
`website/docs/developer-guide/gateway-internals.md`（把 `plugins/platforms/whatsapp/adapter.py`
误标成 Cloud API，实为 Baileys bridge）。

**已知的合法「失效」形态（不要误修）**：树状图内的相对条目（`dingtalk/adapter.py` 在
`plugins/platforms/` 树下）、`~/.hermes/config.yaml` 这类 home 路径、`HERMES_HOME/...` 这类
环境变量前缀路径、跨仓库引用（正文标注 "connector repo"）、示例/占位名（`tools/your_tool.py`、
`test_x.py`）、库名（`discord.py`）、省略号路径（`apps/desktop/.../x.ts`）、扩展名罗列（`.ts`/`.tsx`）。

### 5.9 `sr_tools.py verify` 的分桶语义

校验器只把**第一个桶**当待修项，其余三桶都**不是错误**：

| 桶 | 含义 | 处置 |
|---|---|---|
| ✗ 疑似失效路径 | 多基址都解析不到，且不属于下列任何一类 | **逐条人工判读后再修**（仍可能是合法形态，见 5.8） |
| · 说明性引用 | 该行含「不存在 / 已删除 / 已迁移 / 已移除」等否定词 | 正文已声明不存在，不改 |
| · 非仓库文件名 | 无 `/` 的 `*.yaml|yml|json` | `config.yaml`、`plugin.yaml` 这类运行期配置名 |
| · 裸名缩写 | 无 `/` 但仓库里存在同名文件 | 写法风格（如根 `AGENTS.md` 说 `jobs.py`），不改 |

**工具本身修过的五个缺陷（别再退回去）**：
1. 路径只按 CWD 解析 → 嵌套文档（`apps/desktop/AGENTS.md` 里的 `src/store/composer.ts`）
   全被误报。现按 `.` + 文档自身目录链多基址解析。
2. 正则会把方法名当文件名：`code_kernel.shutdown_kernels_for_delegated_child` 匹配出
   `code_kernel.sh`。现加前后 `[A-Za-z0-9_]` 边界断言（注意**不能**把 `.` 放进后视集，
   否则 `~/.hermes/config.yaml` 又匹配不到）。
3. 报告只打 basename，12 个 `AGENTS.md` 无法区分 → 现打完整路径。
4. **`locate` 看不见 `tests/` 与 `scripts/`**（2026-10-05 修）。原 `SEARCH_ROOTS` 不含这两个目录，
   且 `SKIP_DIRS` 里挂着 `"/tests"`。后果：**测试体系那一篇的每个符号都报「✗ 未找到」**——
   `_hermetic_environment`、`_isolate_hermes_home`、`_effective_file_timeout`、
   `list_os_marked_tests` 全查不到，维护者会被工具**主动误导**。
   现改为**两遍扫描**：先扫生产树，只对第一遍没找到的符号再扫 `tests/` + `scripts/`
   （`FALLBACK_ROOTS`）。这样既能让测试类文档定位到 `tests/conftest.py` 的 fixture，
   又**不会让生产符号的命中被同名测试替身稀释**（实测 `SessionDB` 仍只报 `hermes_state.py:459`）。
5. **`_OS_MARKS` 的教训**（2026-10-05）：该常量已不存在，而文档有 4 处引用它。
   工具查不出「符号不存在」，因为它只校验**文件路径**。
   → 因此本轮补了一道**符号级校验**（见 §八.4），这是 `verify` 之外的独立检查。

**`verify` 的能力边界（务必知道）**：它只校验**文件路径能否解析**，
**不校验 `文件 · 符号 +N` 里的符号是否真在该文件里、偏移是否落在函数体内**。
符号级校验见 §八.4——本轮正是靠它抓出 3 处**符号误归属**（`chat`、`_init_model_routing`
被写成 `cli.py`，实际在 `hermes_cli/cli_*_mixin.py`）。

## 六、收尾校验（每篇写完必做）

```bash
python3 docs/sourceReader/.progress/sr_tools.py verify docs/sourceReader/*.md
```

要求：失效文件路径 = 0（剩余项须能逐条解释为 5.8 的合法形态）；`@数字` 行号引用 = 0；
导航零断链、零孤儿；新增篇目同步进 README 覆盖矩阵与文档地图；`state.json` 的 `base_commit`
更新为当前 HEAD。

---

## 七、2026-10-05 二次刷新的漂移清单（直接用，不必重新侦查）

基准 `cc0a679f14`（2026-09-21）→ `e1fdf003a6`（2026-10-05），**9098 commit / 10106 改动文件**。

### 7.1 本轮的**头号事件**：插件兼容层按计划移除（PR #126164，commit `a5bd246865`）

360 个文件、**−27,749 行**。这条影响面最大，凡涉及"2026-09 大拆分兼容窗口"的段落**全部作废**。

**被移除的东西**：

- **328 个追加的 `PLUGIN-COMPAT` 块**（懒 `__getattr__` 指针表、第三方名再导出、恢复的死定义）
- 3 个再导出桩模块：`gateway/startup_watchdog.py`、`hermes_cli/observability/relay_runtime.py`、
  `tools/environments/modal_utils.py`
- `COMPAT_MANIFEST.md`、`compat_manifest.json`、`scripts/check_compat_pointers.py` 及其 lint 步骤
- **全部上报面**：CLI banner 提示、`hermes plugins compat` 子命令、`hermes doctor` 的兼容性段落、
  更新后提示、Desktop 一次性弹窗、loader 的预导入跳过、`plugins.allow_deprecated_imports` 逃生口
- 树内连带死代码：`hermes_cli/setup.py::_check_espeak_ng`、`gateway/config.py::SessionResetPolicy`
- 6 个测试文件 + `apps/desktop/electron/plugin-compat-notice.ts` 及其测试

**时间线**：兼容层本意是让 pre-#102117 的旧 import 路径活到 **2026-09-14**；窗口关闭两周后
（约 2026-09-28）本提交把层本身删掉。

**现状**：外部插件若仍 import 旧路径，**直接在 `hermes plugins list` 里以 ImportError 报加载失败**，
和任何坏插件走同一条路径——不再有兼容提示。`hermes_cli/plugin_compat.py` **保留**为三个惰性桩
（`compat_report` / `removal_in_effect` / `summary_lines`，共 831 字节），因为"删除前就在跑的
`hermes update`"会在 checkout 换掉之后懒导入它们。

**顺带一个验证过的教训**：两个 `test_run_agent` patch 原先打 `run_agent.handle_function_call`
指针，现在改打 `model_tools.handle_function_call`——**即生产真正读取的那个 seam**。
这正是根 `AGENTS.md` 里"patch where production reads"的实例，写文档时应保留这个例子。

### 7.2 新增的顶层模块（旧文档完全没有）

| 新增 | 内容 | 说明 |
|---|---|---|
| `pm/` | 完整包（`artifact_mirror.py`、`build_env.py`、`downloader.py`、`environment(s).py`、`index_config.py`、`cli.py` …）+ 自带 `AGENTS.md`。**实测 55 文件 / 49 py**，另含 `lock.json`、`uv.lock`、`pyproject.toml`、`artifact-mirror.json`、`termux_runtime_libs.json` | **依赖/环境管理器**（Package Manager）。根 `AGENTS.md` 的 `## Routing Table` 已把它与 `hermes_platform/` 各列一行 |
| `hermes_platform/` | `declaration.py` + `host/`（`facts.py` / `products.py` / `runtime.py`）+ `resolver/`（`app.py` / `availability.py` / `base.py` / `core.py` / `known_dirs.py`）+ 自带 `AGENTS.md`。**实测 14 文件** | **机器事实 + 可执行文件查找** |
| `activate` / `activate.fish` / `activate.ps1` | venv 风格的交互式 shell 激活脚本 | 开发环境入口。根 `AGENTS.md` 的 Development Environment 段落已改写为 `source ./activate` |
| `setup-hermes.ps1` | Windows 安装脚本 | — |
| `hermes_yaml.py`、`hermes_constants_scratch.py` | 新的根级模块 | — |

### 7.3 消失的顶层条目

`COMPAT_MANIFEST.md`、`compat_manifest.json`、`constraints-termux.txt`、`docs/`（上游设计文档，
18 个 md，已被上游清空）。

### 7.4 `hermes_state_*` 兄弟模块：28 → 32（只增不减）

**新增 4 个**：`hermes_state_coverage.py`、`hermes_state_health.py`、`hermes_state_identity.py`、
`hermes_state_pidns.py`。

**没有移除**——根级 `hermes_state_*.py` 在两次基准间只增不减。

> ⚠️ 踩过的坑：用 `git ls-tree -r --name-only <base> | grep -o 'hermes_state_[a-z_]*\.py'`
> 对比会**误报**——`-r` 会扫到 `tests/hermes_state/test_hermes_state_*.py`，
> 于是凭空冒出 6 个"已移除模块"（`compression_locks`、`wal_fallback`、`readonly_preflight`、
> `ux_messages`、`conn_lock_audit`、`compression_busy_retry`）。
> **正确做法**：两边都只取根级——`git ls-tree --name-only <base> | grep '^hermes_state_.*\.py$'`
> 对比 `ls -1 hermes_state_*.py`，并做 `base + added - removed == HEAD` 的算术自检。

（新增的 `coverage` / `health` / `identity` / `pidns` 说明 session 存储侧新增了覆盖率统计、
健康检查、身份与 PID namespace 相关的关注点，刷新 08 篇时要核对，不要沿用旧描述。）

### 7.5 规模变化（用于替换旧数字）

| 模块 | 2026-09-21 | 2026-10-05 |
|---|---|---|
| 根级 `*.py` | 46 | 52 |
| `hermes_state_*.py` | 28 | 32 |
| `agent/` | 301 py | 317 py |
| `hermes_cli/` | 536 py | **644 py**（增幅最大，+108） |
| `gateway/` | 169 py | 177 py |
| `tools/` | 316 py | 339 py |
| `cron/` | 31 py | 36 py |
| `tui_gateway/` | 91 py | 101 py |
| `acp_adapter/` | 14 py | 14 py |
| `plugins/` | 245 py | **225 py**（唯一收缩） |
| `apps/` | 2789 ts/tsx | 3453 ts/tsx |
| `ui-tui/` | 484 ts/tsx | 522 ts/tsx |
| `web/` | 186 ts/tsx | 195 ts/tsx |

### 7.6 本轮确定的 10 处失效路径（全部由 #126164 引起）

`COMPAT_MANIFEST.md`（5 处：01 / 07 / 09 / 14 / 15 篇）与
`scripts/check_compat_pointers.py`（5 处：05 / 07 / 09 / 13 / 14 篇）。
处理方式：不是简单换路径，而是**改写整段语义**——这些文件是被**按计划删除**的，不是搬家。

---

## 八、2026-10-05 刷新执行记录（收尾归档）

### 8.1 结果

| 指标 | 刷新前 | 刷新后 |
|---|---|---|
| 文档数 | 19 | **20**（新增 18 篇） |
| `@行号` 引用 | 0 | **0** |
| ✗ 失效路径 | 10 | **0** |
| 符号级引用 | 未校验 | **542 条解析成功**，3 条为检查器假阳性（见 8.4） |
| 导航断链 | 0 | **0** |
| 孤儿文档 | 0 | **0** |

### 8.2 逐篇处置

| 篇 | 处置 |
|---|---|
| **14** | compat 命中最多（24 行），**§八 整节重写**为「插件兼容层：已按计划移除」；补 `activate` / `setup-hermes.ps1` / `pm` 操作入口 |
| **07** | **§十一 整节重写**为「配置体系与周边机制的边界」；`plugins.allow_deprecated_imports` 配置项已不存在 |
| **09 / 05 / 10 / 13** | compat 段落改写为「层已移除」语义；13 篇另**重写 §四 测试设计原则**（见 8.3） |
| **01 / 15 / README** | 基准改 `e1fdf003a6`、规模数字、矩阵加 `pm/` + `hermes_platform/` 与 18 篇 |
| **00 / 04 / 08 / 17** | 规模数字（28→32、301→317 等）与导航尾 |
| **16** | **更正**其维护者说明：它记录的校验器两个误判**已不复存在**（见 8.3） |
| **18** | **新增**，承接 `pm/` 与 `hermes_platform/` |

### 8.3 本轮额外纠正的三处「非 compat」陈旧内容

这些不在 §七 的清单里，是逐篇核对时新发现的：

1. **13 篇 §四 的权威来源写错了**：原文称「全部来自仓库根 `AGENTS.md`（447 行），是该仓库唯一权威的
   测试哲学表述」。实际根 `AGENTS.md` 已收敛为 **169 行的路由 hub**，测试哲学长文迁到
   **`tests/AGENTS.md`（152 行）**；根 `AGENTS.md` 自己在 `## Rules that apply everywhere` 里写
   「Everything else: `tests/AGENTS.md`」。原文引用的 `§ What we want` / `§ Code Shape Rules` /
   `§ Testing` 三个小节标题**都已不存在**。
2. **13 篇 §4.5 的宿主标记名全部废弃**：`@pytest.mark.linux_only` / `macos_only` / `windows_only`
   已被 `platforms(...)` 取代，且 `tests/_fixtures/platform_gating.py` **主动拒绝**旧标记。
   实测 `platforms("` 用法 **1259 处**，旧标记只剩 9/3/3 处（多数还是「已废弃」的说明文字）。
   同时 `scripts/ci/list_os_marked_tests.py` 的机制也变了：它是**解析 `platforms(...)` 里的 spec
   字符串**，不是按标记名 grep。
3. **16 篇的维护者说明已过期**：它称校验器有两个误判（`.tsx` 被截成 `.ts`；`.sh` 结尾的名字被当
   shell 文件），并为此采用了拆跨度的写法。实测**两个误判都已被 §5.9 的修复消掉**：
   `apps/desktop/src/main.tsx` 整条匹配成功，`tip.show` / `notification.show_nous` 零匹配。
   已在 16 篇就地更正（既有拆分写法无害，不必回改）。

**另外 3 处符号误归属**（由 §8.4 的符号级校验抓出）：

| 位置 | 原文写法 | 实际归属 |
|---|---|---|
| 00 篇 | `cli.py` · `HermesCLI.chat` | `hermes_cli/cli_chat_turn_mixin.py` · `CLIChatTurnMixin.chat +0` |
| 07 篇 | `cli.py` · `HermesCLI._init_model_routing +0` | `hermes_cli/cli_init_mixin.py` · `CLIInitMixin._init_model_routing +0`（`cli.py` 里只有调用点） |
| 13 篇（2 处） | `tests/conftest.py` · `Const:_OS_MARKS` | 该常量**已不存在**；标记真源是 `tests/conftest.py` · `pytest_configure +0` 登记的 `platforms(...)` |

### 8.4 符号级校验（`verify` 之外的独立检查）

`verify` 只解析**文件路径**。要回答「`文件 · 符号 +N` 里的符号是否真在那个文件里」，
需要单独跑一次抽取 + 比对。本轮用的方法（可复现）：

```python
# 记法：`path.py` · `class Name` / `Const:NAME` / `Class.method` / `name`  [+N]
REF = re.compile(
    r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.py)`\s*·\s*"
    r"`(?:class\s+|async\s+def\s+|def\s+|Const:|Module:|Var:)?([A-Za-z_][A-Za-z0-9_.]*)")
DEF  = re.compile(r"^\s*(?:class|def|async def)\s+(\w+)", re.M)   # ← re.M 必需
ASGN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=]+)?=", re.M)
# 比对：sym.split(".")[-1] ∈ (DEF ∪ ASGN)，或 sym 本身在集合里
```

**三个已知假阳性**（不是文档错误，别去改）：

1. **描述调用点**：如 `hermes_cli/_parser.py` · `add("-z", "--oneshot", ...)`——写的是**调用**而非定义；
2. **两个路径用 `·` 分隔**：如 `gateway/run_inbound.py` · `gateway/authz_mixin.py`——抽取器会把
   第二个路径的首段当符号。**建议新写时改用 `、` 或分列**，避免歧义；
3. **`Module:` / `Var:` 前缀后跟路径**：如 `Module:hermes_cli/skills_hub.py` · `Var:_SLASH_ACTIONS`。

> ⚠️ **抽取器自己的坑**：`DEF` 正则**必须带 `re.M`**。漏掉时 `^` 只匹配文件开头，
> 于是几乎全部符号都被判「不存在」——本轮第一次跑就误报 **536 条**失效。
> 写这类检查器时先用已知存在的符号（如 `agent/turn_facade.py` · `TurnFacadeMixin.run_conversation`）
> **自测一遍**再信结果。

### 8.5 仍未解决 / 留待下次

- **偏移 `+N` 的数值正确性未被自动校验**。本轮只校验了「符号存在且归属正确」，
  `+N` 是否真落在预期的函数体内**仍需人工读代码确认**。想做自动化，需要解析 AST 拿到
  函数体行数上界，再断言 `0 <= N <= body_len`。
- **18 篇之外仍无专篇**：`acp_adapter/`、`evals/` 套件设计、`contributors/`（15 篇已诚实标注）。
- `hermes_yaml.py` 与 `hermes_constants_scratch.py` 两个新根级模块的职责未逐行核实
  （14 篇已显式标注）。

