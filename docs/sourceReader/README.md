# Hermes Agent 源码深度文档库（新手重构级指南）

> 状态：已复核（全部行号/符号与基准提交一致）
> 复核日期：2026-08-29
> 生成日期：2026-08-19
> 基准提交：`8f97ae9aec729bcbbad17da462115e1ec1398421`
> 复核方式：2026-08-29 针对基准提交逐一 grep 校验了全部 ~44 个带行号的符号与 ~70 个被引用文件/目录，全部命中；并将 13 篇的测试文件计数 2971 更新为 3054（仓库新增了测试）
> 源码范围：`run_agent.py`、`agent/`、`cli.py`、`hermes_cli/`、`tools/`、`gateway/`、`plugins/`、`hermes_state.py`、`tui_gateway/`、`ui-tui/`、`apps/desktop/`、`cron/`、`tests/`、`scripts/`、`docker/` 等仓库全量
> 生成方式：源码、测试、配置与部署资产静态分析（未运行测试套件）

## 快速摘要

### 架构总览（模块与依赖）

Hermes 是一个个人 AI 代理：同一套 Python 编写的 Agent 核心（`run_agent.py` 的 `AIAgent`）同时驱动四种前端形态——经典 REPL（`cli.py`）、Ink TUI（`ui-tui/` + `tui_gateway/`）、Electron 桌面端（`apps/desktop/` + `web/`）、以及消息网关（`gateway/`，覆盖 Telegram/Discord/Slack 等约 20+ 平台）。

核心依赖方向（底层→上层）：

```
tools/registry.py（零依赖注册表）
   ↑ tools/*.py（121 个工具文件，import 时自注册）
   ↑ model_tools.py（发现 + 分发 handle_function_call）
   ↑ agent/conversation_loop.py（真实对话循环）
   ↑ run_agent.py（AIAgent 门面类）
   ↑ cli.py / tui_gateway/server.py / gateway/run.py / batch_runner.py（各前端入口）
```

横切关注点：`hermes_state.py`（SQLite 会话库）、`hermes_cli/config.py`（config.yaml + .env）、`hermes_logging.py`（日志）、`hermes_constants.py`（profile 感知路径）。能力扩展走 **插件**（`plugins/`）与 **技能**（`skills/`），核心保持"窄腰"。

### 核心调用序列（逐步逻辑）

以 `hermes -z "hello"` 为例的最小主路径（详见 [02-简单例子-全路径走读](./02-简单例子-全路径走读.md)）：

1. `hermes_cli/main.py:main()` — 进程标题、UTF-8、venv 自愈、fast-launch 判断，`argparse` 解析；
2. `hermes_cli/main.py:cmd_chat(args)` — `--in`/`--resume`/`--continue` 解析、cwd 恢复、安全模式；
3. `cli.py:HermesCLI`（或其 TUI 等价路径）— 加载皮肤、命令注册、构造 `AIAgent`；
4. `run_agent.py:AIAgent.run_conversation()` — 转发到真实循环；
5. `agent/conversation_loop.py:run_conversation()` — 组装消息、流式调用 LLM、执行 tool_calls；
6. `model_tools.py:handle_function_call()` — 类型转换、中间件、registry 查表调用工具 handler；
7. 响应文本经流式回调回到前端渲染，消息落盘 `SessionDB`（SQLite）。

### 易错点与边界条件

- **Prompt 缓存神圣不可侵犯**：同一会话内 system prompt / 工具集 / 历史必须字节稳定，禁止中途替换（唯一例外是上下文压缩）；
- **消息角色严格交替**：user/assistant/tool 不能连续同角色，不能在中途注入合成 user 消息；
- **`check_fn` 是进程级 TTL 缓存**：不能用于 per-session 判断；session 级能力门控必须走 toolset（`desktop_ui`/`project` 等）由会话平台属性决定；
- **Session↔workspace 绑定**：resume 时按会话记录的 cwd 恢复目录；`--in` 显式覆盖；
- **持久化租约（durable turn lease）**：多进程共享 `state.db` 时（Desktop、CLI、gateway 并发）需要跨进程串行化 load→run→flush 区段，探针失败要 fail-closed；
- **错误体边界**：工具错误返回模型前截断到 2048 字符（`tools/registry.py:_MAX_TOOL_ERROR_CHARS`），日志保留 8192。

## 阅读顺序（四层推进，不可跳级）

| 层 | 文档 | 目标 |
|---|---|---|
| 0 | [00-阅读指南与文档地图](./00-阅读指南与文档地图.md) | 术语、导航、源码入口索引 |
| 1 | [01-简单框架-系统骨架](./01-简单框架-系统骨架.md) | 进程/模块/依赖/数据主路径 |
| 2 | [02-简单例子-全路径走读](./02-简单例子-全路径走读.md) | 一个真实最小例子走完全链路 |
| 3 | [03-详细逐步说明-主链路拆解](./03-详细逐步说明-主链路拆解.md) | 逐跳拆解 + Mermaid 时序图 |
| 4 | [04](./04-核心模块与类型关系.md) … [15](./15-源码索引与覆盖矩阵.md) | 按模块补齐全部逻辑与技术点 |

## 覆盖矩阵（第四层进度）

| 模块 | 文档 | 状态 |
|---|---|---|
| Agent 核心运行时 | 04 | 已完成 |
| 工具系统 | 06 | 已完成 |
| CLI / TUI | 03/04 | 已完成 |
| 会话状态 | 08 | 已完成 |
| 网关/平台 | 05 | 已完成 |
| 模型提供方 | 04 | 已完成 |
| 插件/技能 | 09 | 已完成 |
| 桌面端/Web | 01/05 | 已完成 |
| 配置 | 07 | 已完成 |
| 定时/后台 | 10 | 已完成 |
| 测试 | 13 | 已完成 |
| 构建部署 | 14 | 已完成 |

> 注：本库生成过程中会持续更新此矩阵；未展开的第四层文档不宣称完成。
