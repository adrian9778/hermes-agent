# Hermes Agent 源码深度文档库（新手重构级指南）

> 状态：已按 `cc0a679f14` 复核
> 复核日期：2026-09-22
> 生成日期：2026-08-19
> 基准提交：`cc0a679f14`（2026-09-21）
> 上一版基准：`aff5125f`（2026-08-29 复核时）/ `8f97ae9aec`（2026-08-17 生成时）
> 源码范围：`run_agent.py`、`agent/`、`cli.py`、`hermes_cli/`、`tools/`、`gateway/`、`plugins/`、`hermes_state*.py`、`tui_gateway/`、`ui-tui/`、`apps/desktop/`、`web/`、`cron/`、`tests/`、`evals/`、`docker/` 等仓库全量
> 生成方式：源码、测试、配置与部署资产静态分析（**未运行测试套件**）

## 快速摘要

### 架构总览（模块与依赖）

Hermes 是一个个人 AI 代理：同一套 Python 编写的 Agent 核心（`run_agent.py` 的 `AIAgent`）同时驱动四种前端形态——经典 REPL（`cli.py`）、Ink TUI（`ui-tui/` + `tui_gateway/`）、Electron 桌面端（`apps/desktop/` + `apps/shared/`）、Web Dashboard（`web/`），以及消息网关（`gateway/` + `plugins/platforms/` 下 **22 个平台插件**）。

核心依赖方向（底层→上层）：

```
tools/registry.py（零依赖注册表）
   ↑ tools/*.py（316 个 py 文件，顶层 261 个，import 时自注册）
   ↑ model_tools.py（发现 + 分发 handle_function_call）
   ↑ agent/conversation_loop.py（真实对话循环）
   ↑ agent/turn_facade.py（turn 准入：租约 + 作用域 + 计量）
   ↑ run_agent.py（AIAgent = 14 个 Mixin 组装）
   ↑ cli.py / tui_gateway/server.py / gateway/run.py / batch_runner.py（各前端入口）
```

横切关注点：`hermes_state.py`（SQLite 会话库，14 Mixin + 28 个兄弟模块）、`hermes_cli/config.py`（config.yaml + .env）、
`hermes_logging.py`（日志）、`hermes_constants.py`（profile 感知路径）。能力扩展走**插件**（`plugins/`，19 个插件目录）
与**技能**（`skills/` 58 个 + `optional-skills/` 150 个），核心保持"窄腰"。

### 核心调用序列（逐步逻辑）

以 `hermes -z "hello"` 为例的最小主路径（详见 [02-简单例子-全路径走读](./02-简单例子-全路径走读.md)）：

1. `hermes` 启动器 → `hermes_cli/main.py` · `main`：进程标题、profile 预解析、UTF-8、venv 自愈、argparse 分发；
2. `hermes_cli/main.py` · `cmd_chat`：安全模式、TUI 判定、会话参数归一化、首跑 bootstrap、provider 守卫；
3. `cli.py` · `class HermesCLI`（**17 个 Mixin**）：加载皮肤、注册命令、`CLIAgentSetupMixin._init_agent` 装配 Agent；
4. `run_agent.py` · `class AIAgent` 的 `__init__` 是**转发器** → `agent/agent_init.py` · `init_agent` 完成真实装配；
5. `agent/turn_facade.py` · `TurnFacadeMixin.run_conversation`：turn 准入（跨进程租约、relay 作用域、计量上下文）；
6. `agent/conversation_loop.py` · `run_conversation`（薄壳）→ `_run_conversation_turn`（实现）；
7. `agent/turn_context.py` · `build_turn_context` 做每轮 setup → LLM 调用 ↔ 工具执行；
8. `model_tools.py` · `handle_function_call` → `tools/registry.py` 查表调用工具 handler；
9. 响应文本经流式回调回前端渲染；消息经 `agent/session_persistence.py` 落盘 `SessionDB`（SQLite）。

### 易错点与边界条件

- **Prompt 缓存神圣不可侵犯**：同一会话内 system prompt / 工具集 / 历史必须字节稳定，禁止中途替换
  （**唯一例外是上下文压缩**，见 [17](./17-上下文压缩与缓存保护.md)）；会改动 system-prompt 状态的斜杠命令
  必须缓存感知——默认延迟失效，`--now` 才立即生效；
- **消息角色严格交替**：user/assistant/tool 不能连续同角色，不能在中途注入合成 user 消息；
- **四大核心类都是 Mixin 组装**：`AIAgent` 14 / `HermesCLI` 17 / `SessionDB` 14 / `GatewayRunner` 17 个 Mixin。
  在 `run_agent.py` / `cli.py` / `hermes_state.py` / `gateway/run.py` 里 grep 方法名常常落空，方法体在 `*Mixin` 文件里；
- **`check_fn` 不是进程级 TTL 缓存**：它是 profile 维度 + 30s TTL + 60s 失败宽限，仍不能表达 per-session 状态；
- **Session↔workspace 绑定**：resume 时按会话记录的 cwd 恢复目录；`--in` 显式覆盖；
- **持久化租约（durable turn lease）**：多进程共享 `state.db` 时（Desktop、CLI、gateway 并发）需要跨进程串行化
  load→run→flush 区段，探针失败要 fail-closed；
- **工具错误体边界**：工具错误返回模型前截断到 2048 字符（`tools/registry.py` · `Const:_MAX_TOOL_ERROR_CHARS`），
  日志侧保留 8192。

## 本版（2026-09-22）更新说明

上一版文档基于 `8f97ae9aec`（2026-08-17）。到本版基准 `cc0a679f14`（2026-09-21）之间隔了
**16321 个 commit**，代码发生了结构性变化，因此本次做了一次系统性更新：

| 变化类型 | 具体表现 |
|---|---|
| **God-file 拆分** | `run_agent.py` 8800+ → 1609 行；`cli.py` 11000+ → 1820 行；`hermes_cli/main.py` 12000+ → 3637 行；`hermes_state.py` 拆成 28 个兄弟模块 |
| **Mixin 组装** | 四大核心类改为 Mixin 组装（14 / 17 / 14 / 17 个） |
| **平台插件化** | 平台适配器从 `gateway/platforms/` 迁到 `plugins/platforms/`，22 个平台各占一个目录 |
| **规模增长** | `tools/` 121 → 316 py；`agent/` 195 → 301 py；`hermes_cli/` 287 → 536 py；`gateway/` 93 → 169 py |
| **上游文档清空** | `docs/` 下 18 个 md 在 HEAD 中已不存在 |

**定位记法迁移**：上一版使用绝对行号，本次更新后全库 117 处行号引用已全部改为
「**符号 + 偏移**」记法（`文件` · `符号` `+N`）。这是为了防止下次上游合并后文档再次整体失效——
代码在函数外增删行不会让符号引用失效。

**本次更新明细**：4 篇重写（00/01/02/03）、12 篇逐篇核对修补（04–15）、**2 篇新增**（16/17）。
更新过程中修正了上一版的大量错误描述，包括 4 个已消失的符号、若干错误常量与错误文件归属。

## 阅读顺序（四层推进，不可跳级）

| 层 | 文档 | 目标 |
|---|---|---|
| 0 | [00-阅读指南与文档地图](./00-阅读指南与文档地图.md) | 术语、定位记法、导航、源码入口索引 |
| 1 | [01-简单框架-系统骨架](./01-简单框架-系统骨架.md) | 进程/模块/依赖/数据主路径 |
| 2 | [02-简单例子-全路径走读](./02-简单例子-全路径走读.md) | 一个真实最小例子走完全链路 |
| 3 | [03-详细逐步说明-主链路拆解](./03-详细逐步说明-主链路拆解.md) | 逐跳拆解 + Mermaid 时序图 |
| 4 | [04](./04-核心模块与类型关系.md) … [17](./17-上下文压缩与缓存保护.md) | 按模块补齐全部逻辑与技术点 |

## 覆盖矩阵（第四层）

| 模块 | 文档 | 本版状态 |
|---|---|---|
| Agent 核心运行时 | [04](./04-核心模块与类型关系.md) | 已更新 |
| 工具系统 | [06](./06-工具系统与工具集.md) | 已更新 |
| CLI / TUI | [03](./03-详细逐步说明-主链路拆解.md) / [16](./16-前端形态与宿主协议.md) | 已更新 |
| 会话状态 | [08](./08-数据模型与会话存储.md) | 已更新 |
| 网关/平台 | [05](./05-消息网关与平台适配.md) | 已更新 |
| 模型提供方 | [04](./04-核心模块与类型关系.md) / [12](./12-错误处理与重试机制.md) | 已更新 |
| 插件/技能 | [09](./09-技能系统与插件架构.md) | 已更新 |
| 桌面端/Web | [16](./16-前端形态与宿主协议.md) | **本版新增** |
| 配置 | [07](./07-配置体系与环境变量.md) | 已更新 |
| 定时/后台 | [10](./10-调度器与定时任务.md) | 已更新 |
| 并发/生命周期 | [11](./11-并发模型与生命周期.md) | 已更新 |
| 上下文压缩 | [17](./17-上下文压缩与缓存保护.md) | **本版新增** |
| 测试 | [13](./13-测试体系与质量保障.md) | 已更新 |
| 构建部署 | [14](./14-构建部署与运维.md) | 已更新 |
| 源码索引 | [15](./15-源码索引与覆盖矩阵.md) | 已更新 |

**已知未覆盖**：`agent/*_adapter.py` 的 provider 适配细节、`agent/billing_*.py` 的完整计费数据模型、
`acp_adapter/`（ACP 协议适配）、`evals/` 评测套件设计细节。这些在 [15 篇](./15-源码索引与覆盖矩阵.md)
的「覆盖缺口」一节中有诚实标注。

## 如何维护本库

本库自带定位与校验工具（在仓库根目录执行）：

```bash
python3 docs/sourceReader/.progress/sr_tools.py locate  SYM [SYM ...]   # 定位符号定义
python3 docs/sourceReader/.progress/sr_tools.py outline FILE --top      # 文件符号骨架
python3 docs/sourceReader/.progress/sr_tools.py offset  FILE SYM        # 符号定义行号
python3 docs/sourceReader/.progress/sr_tools.py verify  docs/sourceReader/*.md          # 校验文档引用
```

**维护前必读**：`docs/sourceReader/.progress/UPDATE-SPEC.md`（记法规范、格式要求、已确认的架构变化与勘误）。

---

_本库面向**重新实现者**，与 `website/docs/`（面向最终用户）互补。仓库根 `AGENTS.md` 是贡献规范与设计意图的权威来源。_
