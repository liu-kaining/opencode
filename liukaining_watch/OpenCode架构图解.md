# OpenCode 架构图解

> **文档版本 v2026.06.15** · 审查日期 2026-06-15  
> **代码基准** · 分支 `dev` · commit `5d0f866` · 包版本 `opencode@1.17.7`  
> 历史快照：[VERSIONS.md](./VERSIONS.md) · 勘误记录：[versions/2026-06-15/META.md](./versions/2026-06-15/META.md)

本文基于仓库实际代码整理。**Mermaid** 块在 GitHub / Cursor 中可直接预览；**PlantUML** 块需 PlantUML 插件或 [plantuml.com](https://www.plantuml.com/plantuml) 渲染，源文件亦在 [`diagram/`](./diagram/) 目录。

---

## 阅读地图

| 层次 | 章节 | 粒度 | 图表类型 |
|------|------|------|---------|
| 鸟瞰 | §1 心智模型 · §2 系统上下文 | 全局 | Mermaid |
| 结构 | §3 Monorepo · §4 分层 · §5 HTTP 路由 | 模块级 | PlantUML + 表格 |
| 核心 | §6 双执行栈 | 架构决策 | Mermaid + 对照表 |
| 深潜 | §7 V1 路径 · §8 V2 路径 · §9 Coordinator · §10 Provider Turn | 调用链 | PlantUML 时序/活动 |
| 机制 | §11 EventV2 · §12 Location · §13 工具权限 · §14 子 Agent | 子系统 | PlantUML + Mermaid |
| 专题 | §15 Context Epoch · §16 Compaction · §17 Agent | 专题 | Mermaid |
| 索引 | §18 源码 · §19 认知要点 | 查阅 | 表格 |

---

## 1. 心智模型

OpenCode 是 **Bun workspaces monorepo** 开源 AI 编程 Agent。本地运行时核心是 `packages/opencode`（CLI + HTTP）+ `packages/core`（V2 Session 引擎 + SQLite）。

**当前代码态（2026-06-15）的关键事实：** 同一 HTTP Server（默认 `:4096`）上 **并存两套 Session 执行栈 + 两套 HTTP API**。

```
┌─ 交互路径（TUI / Web / Desktop 日常聊天）────────────────────────────┐
│  sdk.client.session.prompt()                                           │
│  → POST /session/{id}/message                                          │
│  → SessionPrompt (V1) → SessionProcessor → LLM (AI SDK)                │
└────────────────────────────────────────────────────────────────────────┘

┌─ Durable 路径（V2 HttpApi / Public API / 演进方向）────────────────────┐
│  client.v2.session.prompt()                                            │
│  → POST /api/session/{id}/prompt                                       │
│  → SessionV2.prompt → SessionInput.admit → SessionExecution.wake       │
│  → SessionRunner → llm.stream → ToolRegistry → EventV2 → SQLite        │
└────────────────────────────────────────────────────────────────────────┘
```

**架构约束（读源码时的锚点）：**

| 约束 | 含义 |
|------|------|
| 准入 ≠ 执行（V2） | `SessionInput.admit` 写 durable inbox；`SessionExecution.wake` 异步调度 |
| 每 Session 一条 drain | `SessionRunCoordinator` 合并 wake、处理 interrupt 边界 |
| 每 turn 一次 LLM（V2） | `SessionRunner.runTurnAttempt` 只调一次 `llm.stream` |
| Location 作用域 | Runner / Tools / Config 按项目目录隔离 |
| 进程全局 | `SessionStore` / `SessionExecution` / `EventV2` 仅按 sessionID 路由 |
| 子 Agent | `task` 工具 + `parentID` 子 Session，非独立 Runner 类型 |

---

## 2. 系统上下文（C4 Context）

```mermaid
flowchart TB
  subgraph Actors["使用者 / 集成方"]
    Dev["开发者"]
    Bot["Slack / GitHub Action"]
    Ext["第三方 via SDK"]
  end

  subgraph OpenCodeLocal["OpenCode 本地运行时"]
    CLI["CLI / TUI"]
    Web["Web / Desktop App"]
    Engine["Session 引擎 + Tools + LLM"]
    DB[("SQLite")]
  end

  subgraph External["外部依赖"]
    LLMProv["LLM Providers\nOpenAI / Anthropic / Gemini / Bedrock"]
    MCP["MCP Servers"]
    LSP["Language Servers"]
  end

  subgraph Cloud["云端产品 (SST, 独立部署)"]
    Console["Console · 认证/计费"]
    Ent["Enterprise"]
  end

  Dev --> CLI
  Dev --> Web
  Bot --> Ext
  Ext --> Engine
  CLI --> Engine
  Web --> Engine
  Engine --> DB
  Engine --> LLMProv
  Engine --> MCP
  Engine --> LSP
  Console -.->|账号/模型配置| Dev
```

**边界说明：**

- UI 层（`tui` / `app` / `desktop`）**只通过 `@opencode-ai/sdk` 访问 HTTP**，不 import `@opencode-ai/core`。
- `@opencode-ai/server` 是 **路由契约 + handlers 包**，handlers 挂载在 opencode 进程内，不是独立微服务。
- Cloud 包与本地引擎解耦，本地 `opencode serve` 可完全离线运行。

---

## 3. Monorepo 包拓扑

```plantuml
@startuml opencode-packages
!theme plain
skinparam componentStyle rectangle
title Monorepo 包依赖（核心路径）

package "Clients" {
  [tui] as tui
  [app] as app
  [desktop] as desk
  [sdk/js] as sdk
}

package "Runtime · packages/opencode" #E3F2FD {
  [CLI yargs] as cli
  [HTTP Server] as http
  [SessionPrompt V1] as sp
  [SessionProcessor] as proc
  [opencode ToolRegistry] as otools
  [MCP / LSP / Plugin] as integ
}

package "Engine · packages/core" #F3E5F5 {
  [SessionV2] as sv2
  [SessionRunner] as runner
  [EventV2 + Projector] as ev
  [LocationServiceMap] as loc
  [core ToolRegistry] as ctools
  database "SQLite" as db
}

package "Contracts" {
  [server] as srv
  [llm] as llm
  [plugin] as plug
}

tui --> sdk
app --> sdk
desk --> app
desk --> http
sdk --> http
cli --> http

http --> srv
http --> sp
srv --> sv2
sp --> proc
sp --> otools
proc --> llm

sv2 --> runner
runner --> loc
runner --> ctools
runner --> llm
ev --> db
sp --> ev : EventV2Bridge

http --> integ
loc --> ctools

@enduml
```

| 包 | 职责 |
|----|------|
| `opencode` | CLI、HTTP Server、Instance Bootstrap、V1 Session 编排 |
| `@opencode-ai/core` | V2 Session、EventV2、Location 层、Drizzle/SQLite |
| `@opencode-ai/server` | HttpApi 路由定义 + V2 handlers（`/api/*`） |
| `@opencode-ai/llm` | Effect Schema LLM 协议、Provider 路由 |
| `@opencode-ai/sdk` | 生成的 HTTP 客户端（Instance + V2 双 surface） |
| `tui` / `app` / `desktop` | UI，SDK-only 边界 |

---

## 4. 运行时分层

七层模型：**由外向内，职责逐层收窄**。

```mermaid
flowchart TB
  L0["L0 客户端\nTUI · Web · Desktop · SDK 集成"]
  L1["L1 传输 & 实例\nHTTP :4096 · InstanceContext · Bootstrap"]
  L2["L2 Location\nLocationServiceMap · 按 directory 隔离"]
  L3["L3 Session 编排\nV1 SessionPrompt ∥ V2 SessionV2/Runner"]
  L4["L4 持久化\nEventV2 · SessionProjector · SQLite"]
  L5["L5 LLM\n@opencode-ai/llm · AI SDK 兼容层(V1)"]
  L6["L6 能力\nTools · Permission · MCP · LSP · Plugin"]
  L7["L7 控制面/云\nWorkspace 路由 · Console · Enterprise"]

  L0 --> L1 --> L2
  L1 --> L3
  L2 --> L3
  L3 --> L4
  L3 --> L5
  L2 --> L6
  L3 --> L6
  L1 --> L7
```

**L1 Instance 层要点：**

- 请求通过 `x-opencode-directory` 或 `?directory=` 绑定项目目录。
- `InstanceBootstrap` 启动：Config、Plugins、LSP、VCS、Snapshot、Format。
- `InstanceState` / `InstanceStore` 按目录缓存服务实例。

**L2 vs L3 作用域分裂（V2 设计核心）：**

| 作用域 | 组件 | 设计意图 |
|--------|------|---------|
| 进程全局 | SessionStore, SessionExecution, EventV2 | 仅持有 sessionID，便于跨 Location 路由 |
| Location | SessionRunner, ToolRegistry, AgentV2, Config | 与 filesystem / 权限 / 工具绑定 |

---

## 5. HTTP Server 路由与实例模型

opencode 在 **单个进程** 内组装多棵路由树（`httpapi/server.ts`）：

| 路由树 | 前缀 | Handler | Session 入口 |
|--------|------|---------|-------------|
| RootHttpApi | `/global/*`, control | global / control-plane | — |
| **InstanceHttpApi** | `/session/*`, `/config/*`, … | `handlers/session.ts` 等 | **SessionPrompt (V1)** |
| **Api (@opencode-ai/server)** | `/api/session/*`, `/api/agent/*`, … | `packages/server/handlers` | **SessionV2** |
| EventApi | SSE | eventHandlers | 事件流 |
| Raw | `/*` UI, Pty WS | uiRoute, ptyConnect | — |

PlantUML 组件视图（源文件 [`diagram/http-server-routes.puml`](./diagram/http-server-routes.puml)）：

```plantuml
@startuml opencode-http-server-routes
!theme plain
skinparam componentStyle rectangle

package "opencode 进程 · 默认 :4096" {
  [HttpApiApp] as app
  package "InstanceHttpApi" { [sessionHandlers\n/session/* → V1] as inst }
  package "Api @opencode-ai/server" { [SessionHandler\n/api/session/* → V2] as v2api }
  package "Raw" { [uiRoute] [PtyConnectApi] }
}
[SDK / TUI / Web] --> app
app --> inst
app --> v2api
note bottom of inst : POST /session/{id}/message
note bottom of v2api : POST /api/session/{id}/prompt
@enduml
```

**SDK 与路由的精确映射：**

| SDK 调用 | HTTP | 执行栈 |
|----------|------|--------|
| `client.session.prompt({ parts, agent, model })` | `POST /session/{id}/message` | V1 |
| `client.session.promptAsync(...)` | `POST /session/{id}/prompt_async` | V1 异步 |
| `client.v2.session.prompt({ prompt, delivery })` | `POST /api/session/{id}/prompt` | V2 |

源码：`packages/sdk/js/src/v2/gen/sdk.gen.ts`（Session2 vs Session3）。

---

## 6. 双执行栈

这是理解整个项目 **_migration 现状_** 的核心章节。

### 6.1 对照表

| 维度 | V1 交互栈 | V2 Durable 栈 |
|------|----------|--------------|
| 入口 | `SessionPrompt.prompt` / `loop` | `SessionV2.prompt` |
| 编排 | `SessionProcessor.process` | `SessionRunner.run` → `runTurnAttempt` |
| LLM | `opencode/session/llm.ts`（AI SDK） | `core/session/runner/llm.ts`（native route） |
| 工具 | `opencode/tool/registry.ts` | `core/tool/registry.ts` |
| 持久化 | MessageV2 + Storage；可选镜像 EventV2 | EventV2 同步事件 → Projector |
| 主要调用方 | TUI、Web 聊天、TaskTool 子 Session | V2 HttpApi、Public API、core 测试 |
| 规格 | 隐含于 opencode 实现 | `specs/v2/session.md` |

### 6.2 汇合点：EventV2 + SQLite

```mermaid
flowchart LR
  subgraph V1["V1 栈"]
    SP["SessionPrompt"]
    PR["SessionProcessor"]
    BR["EventV2Bridge\n始终加载"]
  end

  subgraph V2["V2 栈"]
    SV2["SessionV2"]
    RN["SessionRunner"]
    EV["EventV2 原生 publish"]
  end

  subgraph Store["共享持久化"]
    PJ["SessionProjector"]
    DB[("SQLite")]
  end

  SP --> PR
  PR --> BR
  PR -.->|OPENCODE_EXPERIMENTAL_EVENT_SYSTEM| EV
  SV2 --> RN --> EV
  BR --> EV
  EV --> PJ --> DB
```

**EventV2Bridge 职责澄清：**

- **始终加载**（`app-runtime.ts`）：为 `EventV2.publish` 自动注入 Instance `location`；转发到 `GlobalBus`。
- **`OPENCODE_EXPERIMENTAL_EVENT_SYSTEM`**：控制 V1 `SessionProcessor` **是否额外镜像** Step/Tool 到 EventV2（`mirrorAssistant`），不是 Bridge 开关。

---

## 7. V1 交互路径（细节）

TUI 发消息的完整调用链：

```plantuml
@startuml v1-tui-prompt
!theme plain
title V1 路径 · TUI 发消息

actor TUI
participant "SDK Session2" as SDK
participant "InstanceHttpApi" as HTTP
participant "SessionPrompt" as SP
participant "SessionRunState" as RS
participant "SessionProcessor" as Proc
participant "LLM (AI SDK)" as LLM
participant "opencode ToolRegistry" as Tools
participant "EventV2Bridge" as Bridge

TUI -> SDK: client.session.prompt(sessionID, parts, agent, model)
SDK -> HTTP: POST /session/{id}/message
HTTP -> SP: prompt(input)

SP -> RS: ensureRunning(sessionID)
SP -> SP: runLoop(sessionID)

loop 每 model step
  SP -> SP: filterCompacted history\nhandleSubtask / compaction
  SP -> Tools: SessionTools.resolve()
  SP -> Proc: process(llm.stream)
  Proc -> LLM: stream(request)

  loop stream events
    Proc -> Proc: handleEvent\npersist parts
    alt tool-call
      Proc -> Tools: execute via AI SDK tool()
      Proc -> LLM: tool-result
    end
    opt experimentalEventSystem
      Proc -> Bridge: mirror Step/Tool → EventV2
    end
  end
end

HTTP --> SDK: stream JSON message
SDK --> TUI: UI 更新 via SSE global.event

@enduml
```

**V1 特征：**

- 内存循环 `SessionPrompt.runLoop`，工具在 Processor 内 inline settle。
- 子 Agent（`task` 工具）对子 Session 递归调用 **同一 V1 路径**。
- Compaction / Revert / Share 等能力仍在 V1 HTTP surface。

---

## 8. V2 Durable 路径（细节）

### 8.1 Prompt 准入 → 调度

```plantuml
@startuml v2-prompt-admission
!theme plain
title V2 · Prompt 准入与调度

participant Client
participant "SessionV2" as SV2
participant "SessionInput" as SI
participant "EventV2" as EV
participant "SessionProjector" as PJ
participant "SessionExecution" as SE
participant "SessionRunCoordinator" as SC
database SQLite as DB

Client -> SV2: prompt(sessionID, prompt, delivery, resume?)

SV2 -> SI: admit()
SI -> EV: PromptLifecycle.Admitted
EV -> PJ: project → session_input row
EV -> DB: txn commit

alt resume != false
  SV2 -> SE: wake(sessionID, admittedSeq)
  note right: fork 异步，不阻塞 HTTP 响应
  SE -> SC: wake(key, seq)
else resume == false
  note right: 仅 durable admit，不调度
end

Client <-- SV2: Admitted receipt

@enduml
```

### 8.2 Delivery 语义

| 模式 | 行为 |
|------|------|
| `steer`（默认） | 合并进当前 activity；在下一 **safe provider-turn boundary** 由 Runner `promoteSteers` |
| `queue` | FIFO；当前 activity 结束后 `promoteNextQueued` 开新 activity |

`session_input` 是 durable inbox；**Promoted 之前对模型不可见**。

### 8.3 端到端数据流（Mermaid 总览）

```mermaid
flowchart TB
  subgraph Admission["① Durable Admission"]
    A1["SessionV2.prompt"] --> A2["SessionInput.admit"]
    A2 --> A3["Event: Admitted"]
    A3 --> A4[("session_input")]
  end

  subgraph Schedule["② Advisory Schedule"]
    S1["SessionExecution.wake"] --> S2["RunCoordinator"]
  end

  subgraph Run["③ Location-scoped Run"]
    R1["Runner.run"] --> R2["promote + Context Epoch"]
    R2 --> R3["materialize tools"]
    R3 --> R4["llm.stream"]
    R4 --> R5["settle tools"]
    R5 --> R1
  end

  subgraph Project["④ Projection"]
    P1["EventV2 txn"] --> P2[("session_message")]
  end

  A1 --> S1
  S1 --> R1
  A3 --> P1
  R4 --> P1
  P2 --> SSE["SessionV2.events SSE"]
```

---

## 9. SessionRunCoordinator 状态机

进程内 **每个 Session ID 最多一条 active drain chain**；不同 Session 可并发 drain。

```plantuml
@startuml opencode-coordinator-fsm
!theme plain
[*] --> Idle
Idle --> Draining : run() / wake()
Draining --> Draining : coalesced wake
Draining --> DrainingPending : run() 升级 pending
DrainingPending --> Draining : coalesced rerun
Draining --> Idle : drain 完成
DrainingPending --> Idle : drain 完成
Draining --> Interrupted : interrupt(seq)
Interrupted --> Idle : cleanup
note right of Draining : 每 Session 一条 drain chain
@enduml
```

| 操作 | 语义 |
|------|------|
| `run(sessionID)` | 显式 drain；加入当前 chain 或启动新 chain |
| `wake(sessionID, seq?)` | advisory；idle 时启动，draining 时 coalesce 为一次 pending rerun |
| `interrupt(sessionID, seq?)` | 停止 active fiber；suppress interrupt 边界前的 stale wake |
| `resume(sessionID)` | 等价于 force run，处理 durable inbox 中 pending 工作 |

实现：`packages/core/src/session/execution/local.ts` → `SessionRunCoordinator` → `SessionRunner.run({ force? })`。

---

## 10. SessionRunner · 单次 Provider Turn

V2 与 V1 的根本差异：**每 turn 恰好一次 `llm.stream`**，工具在 stream  handler 内 eager fiber settle，turn 结束前 await 全部 fibers。

```plantuml
@startuml opencode-v2-provider-turn
!theme plain
|SessionRunner| start
:runTurnAttempt;
:Location 校验 + AgentV2.select;
:Context Epoch + promote input;
:SessionHistory + compactIfNeeded;
:materialize tools + llm.stream;
while (stream?) is (event)
  if (tool-call) then
    :settle fiber + tool-result;
  else (delta)
    :live-only publish;
  endif
endwhile
:await fibers + reload history;
stop
@enduml
```

**硬限制与边界行为：**

| 项 | 值 / 行为 |
|----|----------|
| `MAX_STEPS` | 25 provider turns / drain |
| Location 迁移 | Session 已 move 到其他 Location → interrupt |
| 中断工具 | 上次 crash 遗留 `running` 工具 → `Tool execution interrupted` |
| Overflow | `compactAfterOverflow` 最多重建一次 logical turn |

Runner 内待办清单见 `runner/llm.ts` 文件头注释（`[x]` / `[ ]` 跟踪 V2 parity）。

---

## 11. EventV2 事件溯源

### 11.1 两类事件

| 类型 | 持久化 | 投影 | 回放 | 示例 |
|------|--------|------|------|------|
| Sync | ✅ | ✅ DB 事务内 | ✅ | Admitted, Promoted, Tool.Success |
| Live-only | ❌ | ❌ | ❌ | Text.Delta, Reasoning.Delta, Compaction progress |

### 11.2 同步事件提交管道

```plantuml
@startuml eventv2-commit
!theme plain
title EventV2.commitSyncEvent 管道

start
:EventV2.publish(sync event);

:beforeCommit guards\n例: SessionInput.guardReservedID;

partition "DB Transaction" {
  :run registered projectors;
  :SessionProjector 更新读模型;
  :insert event row;
  :bump aggregate sequence;
}

:notify aggregate subscribers;
:GlobalBus / SSE 推送;

stop

@enduml
```

### 11.3 Session 事件词汇（精选）

| 事件 | 投影目标 |
|------|---------|
| `PromptLifecycle.Admitted` | `session_input` inbox row |
| `PromptLifecycle.Promoted` | 可见 user `session_message` |
| `Step.Started/Ended` | assistant turn 边界 |
| `Text.*` / `Reasoning.*` | message parts |
| `Tool.Input/Called/Success/Failed` | tool parts + 状态 |
| `ContextUpdated` | Context Epoch 推进 |
| `Compaction.started/ended` | 压缩 checkpoint |
| `InterruptRequested` | 中断信号 |

读路径：`SessionV2.events({ after })`（SSE）· `SessionHistory.entriesForRunner()`（Runner）。

---

## 12. LocationServiceMap

打开项目目录时 boot 的 Effect Layer 集合（`location-layer.ts`），**Idle TTL 60 分钟**。

```plantuml
@startuml location-services
!theme plain
title LocationServiceMap 服务分层

rectangle "Location.Ref\n{ directory, workspaceID? }" as loc

package "Base" #E0F2F1 {
  [Config] [AgentV2] [PluginV2] [Catalog]
  [FileSystem] [Watcher] [Pty] [SkillV2]
  [SystemContextBuiltIns] [Reference] [CommandV2]
}

package "Permission & Tools" #E8F5E9 {
  [PermissionV2] [PermissionSaved]
  [ToolRegistry] [ToolOutputStore]
}

package "Execution" #F3E5F5 {
  [SessionRunnerModel]
  [SessionRunner]
  [BuiltInTools]
  [SkillGuidance] [ReferenceGuidance]
}

package "Auxiliary" #FFF3E0 {
  [SessionTodo] [QuestionV2]
  [Image] [FileMutation]
}

loc --> Base
Base --> "Permission & Tools"
"Permission & Tools" --> Execution
Base --> Auxiliary

note bottom
  **进程全局（不在 Location 内）**
  SessionStore · SessionExecution · EventV2
  ApplicationTools 注册入口

  Boot 副作用: ProjectCopy.refreshAfterBoot
end note

@enduml
```

**SessionExecution 路由链（仅 sessionID）：**

```
SessionExecution.wake(sessionID)
  → SessionStore.get(sessionID) → location
  → LocationServiceMap.get(location)
  → SessionRunner.run({ sessionID })
```

---

## 13. 工具注册与权限

### 13.1 双 Registry

| | V1 (`opencode`) | V2 (`core`) |
|---|----------------|------------|
| 形态 | AI SDK `tool()` 包装 | `Tool.make` + Effect execute |
| 解析 | `SessionTools.resolve` | `ToolRegistry.materialize` |
| 执行 | Processor inline | `settle()` fiber + `permission.assert` |

### 13.2 V2 工具生命周期

```mermaid
flowchart TB
  subgraph Register["注册阶段"]
    BI["BuiltInTools.locationLayer"]
    APP["ApplicationTools 进程全局"]
    PLG["Plugin register"]
    REG["ToolRegistry.register overlay"]
  end

  subgraph Turn["每 Provider Turn"]
    MAT["materialize(permissions)"]
    FIL["过滤 wholly-denied\n(visibility only)"]
    DEF["definitions + settle hook → LLM"]
  end

  subgraph Settle["Tool Call"]
    CALL["llm stream tool-call"]
    ST["settle(call)"]
    PERM["PermissionV2.assert"]
    EXEC["Tool.execute"]
    OUT["ToolOutputStore.bound"]
    EVT["Tool.Success / Failed"]
  end

  BI --> REG
  PLG --> REG
  APP --> MAT
  REG --> MAT --> FIL --> DEF
  DEF --> CALL --> ST --> PERM
  PERM -->|allow| EXEC --> OUT --> EVT
  PERM -->|deny| DENY["DeniedError"]
  PERM -->|ask| ASK["permission.v2.asked → 用户"]
```

**权限规则合并：** Agent 默认 ruleset + Session `PermissionSaved` + Subagent 继承；**最后匹配的 wildcard 规则胜出**；默认 effect 为 `ask`。

---

## 14. 子 Agent（task 工具）

Subagent **不是**独立 Runner 类型，而是 `parentID` 关联的普通 Session。

```plantuml
@startuml subagent-task
!theme plain
title 子 Agent · task 工具

participant "Primary Session\n(build/plan)" as Parent
participant "TaskTool" as Task
participant "Agent registry" as Agent
participant "Sub Session\n(parentID=父)" as Child
participant "SessionPrompt V1" as SP

Parent -> Task: tool-call(subagent_type, prompt, background?)
Task -> Agent: get(subagent_type)\nmode must be subagent

alt 新任务
  Task -> Child: Session.create(parentID)
else resume
  Task -> Child: 复用 task_id 对应 Session
end

Task -> Task: deriveSubagentSessionPermission()

alt foreground (default)
  Task -> SP: prompt(childSession)
  SP -> SP: runLoop → 完成
  Task --> Parent: tool-result XML
else background
  note right: OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS
  Task --> Parent: 立即返回 task id
  SP -> SP: 异步 runLoop
  SP --> Parent: 完成后注入 synthetic result
end

@enduml
```

| subagent | mode | 能力概要 |
|----------|------|---------|
| `general` | subagent | 多步研究；deny todowrite |
| `explore` | subagent | 只读探索；deny edit/bash 等 |

源码：`packages/opencode/src/tool/task.ts` · `agent/subagent-permissions.ts`。

---

## 15. Context Epoch

V2 Session 持久化 **模型可见的特权系统上下文**（与 user/assistant 消息分离）。

**Context Sources：** 环境事实 · 主机日期 · `AGENTS.md` · Agent Skills 指引 · Location 注册源

```mermaid
flowchart TB
  subgraph Sources["Context Sources"]
    S1["Environment / Date"]
    S2["AGENTS.md upward"]
    S3["Skill Guidance"]
    S4["Registry sources"]
  end

  subgraph Epoch["Context Epoch"]
    B["Baseline 不可变快照"]
    SN["Snapshot 结构化对比"]
    U["Chronological Updates"]
  end

  Sources --> OBS["observe at safe boundary"]
  OBS --> INIT["initialize epoch"]
  INIT --> B
  PROM["promote input"] --> REC["reconcile"]
  REC -->|changed| UPD["ContextUpdated + advance snapshot"]
  REC -->|unchanged| REQ["assemble LLM request"]
  UPD --> U --> REQ
  B --> REQ

  subgraph Triggers["Epoch 替换"]
    T1["Agent / Model switch"]
    T2["Compaction ended"]
    T3["Session Move → clear"]
  end

  Triggers --> REC
```

规格：`specs/v2/session.md` · `specs/v2/instructions.md`。

---

## 16. Compaction

V2 Runner **已实现**自动压缩（`SessionCompaction.compactIfNeeded`）。

```mermaid
flowchart TB
  START["runTurnAttempt 开始前"] --> EST["估算 model-visible tokens"]
  EST --> CHECK{"> contextWindow - reserve?"}
  RES["reserve = max(outputAllowance, compaction.buffer)"]
  CHECK -->|否| TURN["执行 provider turn"]
  CHECK -->|是| COMP["Compaction hidden agent"]
  COMP --> CS["compaction.started"]
  CS --> CE["compaction.ended\nsummary + recent context"]
  CE --> EPO["Context Epoch replacement"]
  EPO --> RELOAD["reload history"] --> TURN

  TURN --> OV{"Provider overflow?"}
  OV -->|是| OFC["compactAfterOverflow"]
  OFC -->|成功| RELOAD
  OFC -->|第二次失败| FAIL["终端 Step.Failed"]

  note1["完整 transcript 保持 durable\nactive representation 被 checkpoint 替换"]
```

---

## 17. Agent 模型

```mermaid
flowchart LR
  subgraph Primary["primary · UI 可选"]
    build["build 默认"]
    plan["plan 受限 edit"]
  end

  subgraph Sub["subagent · 仅 task"]
    general["general"]
    explore["explore"]
  end

  subgraph Hidden["primary + hidden · 内部"]
    compact["compaction"]
    title["title"]
    summary["summary"]
  end

  Primary --> Sel["AgentV2.select()\nmode≠subagent ∧ !hidden"]
  Sub --> Task["task 工具"]
```

`AgentV2.select(id?)`：`packages/core/src/agent.ts` · 内置定义 `packages/core/src/plugin/agent.ts`。

---

## 18. 源码索引

| 主题 | 路径 |
|------|------|
| HTTP 路由组装 | `packages/opencode/src/server/routes/instance/httpapi/server.ts` |
| Instance Session HTTP | `packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts` |
| V2 Session HTTP | `packages/server/src/handlers/session.ts` |
| SDK Instance prompt | `packages/sdk/js/src/v2/gen/sdk.gen.ts` → `/session/{id}/message` |
| SDK V2 prompt | 同文件 → `/api/session/{id}/prompt` |
| V1 SessionPrompt | `packages/opencode/src/session/prompt.ts` |
| V1 Processor | `packages/opencode/src/session/processor.ts` |
| V2 Session API | `packages/core/src/session.ts` |
| SessionInput | `packages/core/src/session/input.ts` |
| SessionExecution | `packages/core/src/session/execution/local.ts` |
| RunCoordinator | `packages/core/src/session/run-coordinator.ts` |
| SessionRunner | `packages/core/src/session/runner/llm.ts` |
| EventV2 | `packages/core/src/event.ts` |
| SessionProjector | `packages/core/src/session/projector.ts` |
| EventV2Bridge | `packages/opencode/src/event-v2-bridge.ts` |
| Location layers | `packages/core/src/location-layer.ts` |
| core ToolRegistry | `packages/core/src/tool/registry.ts` |
| TaskTool | `packages/opencode/src/tool/task.ts` |
| V2 规格 | `specs/v2/session.md` |

---

## 19. 架构认知要点

读代码或对照本文时，以下结论已与 **dev@5d0f866** 源码核对：

| 常见误解 | 实际情况 |
|---------|---------|
| TUI 已走 `SessionV2.prompt` | TUI 走 `POST /session/{id}/message` → V1 SessionPrompt |
| `@opencode-ai/server` 是独立服务 | 路由包；handlers 挂载在同一 opencode HTTP 进程 |
| EventV2Bridge 是实验功能 | Bridge 始终加载；实验 flag 控制 V1 Processor **额外镜像** |
| V2 不能做 Compaction | Runner 已有 `compactIfNeeded` + overflow recovery |
| Subagent 有独立 Runner | 普通 Session + `task` 工具 + V1 Prompt 循环 |

**演进方向（规格层）：** V2 Runner 完全替代 V1 `SessionPrompt.loop`；保留 admission/execution 分离、一次 `llm.stream`/turn。Parity 进度见 `specs/v2/session.md` 中 V1 Runtime Context Parity 表。

**文档维护：** 架构变更后新建 `versions/YYYY-MM-DD/` 快照，见 [VERSIONS.md](./VERSIONS.md)。

---

*对照 dev@5d0f866 · opencode@1.17.7 · 2026-06-15*
