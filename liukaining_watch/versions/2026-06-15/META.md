# 版本快照元数据 — 2026-06-15

| 字段 | 值 |
|------|-----|
| 快照日期 | 2026-06-15 |
| 文档版本 | v2026.06.15 |
| Git 分支 | `dev` |
| Git Commit | `5d0f86606ac30690f79f0a6a9f41a1f49fe95d0b` |
| Commit 时间 | 2026-06-14 22:36:21 -0400 |
| Commit 说明 | fix(mcp): stop idle OAuth callback server (#32245) |
| npm 包版本 | `opencode` **1.17.7** |
| Bun | 1.3.14 |

## 审查方法

2026-06-15 二次审查，逐条对照以下源码：

- `packages/opencode/src/server/routes/instance/httpapi/server.ts` — 双路由树挂载
- `packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts` — Instance API → SessionPrompt
- `packages/server/src/handlers/session.ts` — V2 HttpApi → SessionV2.prompt
- `packages/sdk/js/src/v2/gen/sdk.gen.ts` — TUI 实际调用的 SDK 路径
- `packages/tui/src/component/prompt/index.tsx` — TUI prompt 调用
- `packages/opencode/src/event-v2-bridge.ts` — EventV2Bridge 职责
- `packages/opencode/src/session/processor.ts` — experimentalEventSystem 作用
- `packages/core/src/session/runner/llm.ts` — V2 Runner + Compaction
- `packages/opencode/src/tool/task.ts` — 子 Agent

## 本版相对初稿的勘误

| # | 初稿问题 | 修正 |
|---|---------|------|
| 1 | 「TUI 走 V1、server 走 V2」过于简化 | 同一 HTTP Server 挂载 **两套 API**：Instance `/session/*`（V1）+ V2 `/api/session/*` |
| 2 | TUI 调用路径未说明 | TUI 用 `sdk.client.session.prompt()` → `POST /session/{id}/message` → `SessionPrompt` |
| 3 | EventV2Bridge 描述为「实验性双写迁移」 | Bridge **始终加载**；`OPENCODE_EXPERIMENTAL_EVENT_SYSTEM` 控制 V1 Processor **额外**镜像 Step/Tool 到 EventV2 |
| 4 | V2 Compaction 描述模糊 | V2 Runner **已实现** `SessionCompaction.compactIfNeeded` 与 overflow recovery |
| 5 | `@opencode-ai/server` 像独立服务 | 它是路由定义包，handlers **挂载在 opencode HTTP Server 内** |

## 本版已验证的关键断言

- [x] 准入与执行分离：`SessionInput.admit` + `SessionExecution.wake`
- [x] MAX_STEPS = 25（`packages/core/src/session/runner/llm.ts`）
- [x] 子 Agent 通过 `task` 工具 + `parentID` 子 Session
- [x] LocationServiceMap 60min idle TTL
- [x] 默认端口 4096（`packages/opencode/test/server/httpapi-listen.test.ts`）
- [x] 实例路由 header/query：`x-opencode-directory` 或 `?directory=`

## 已知快速变化区域

- V1 → V2 迁移进行中，Instance API 与 V2 HttpApi 并存
- `specs/v2/session.md` 中 V1 Runtime Context Parity 表仍有多项 `partial` / `missing`
- SDK 中 `Session2`（Instance）与 `Session3` / `client.v2.session`（V2 HttpApi）并存

## v2026.06.15 第四次修订

- 主文档图表 **全部统一为 PlantUML**（移除 Mermaid）
- 修复 §5 / §12 PlantUML 语法（alias、note 锚点、避免 `*/` 和 `{}`）
- §1 心智模型改为 PlantUML 组件图

## v2026.06.15 第三次修订

- 移除文档中「分享」相关章节与措辞
- 重构为「鸟瞰 → 结构 → 深潜 → 机制」四层阅读地图
- 新增 PlantUML：HTTP 路由树、V1 TUI 时序、V2 准入、Coordinator FSM、Provider Turn、EventV2 提交、Location 分层、Subagent 时序
- Mermaid 保留：C4 上下文、双栈汇合、V2 数据流、工具生命周期、Context Epoch、Compaction、Agent 模型
