# liukaining_watch

OpenCode 项目架构图解与版本快照。

## 入口

| 文件 | 说明 |
|------|------|
| **[OpenCode架构图解.md](./OpenCode架构图解.md)** | 主文档：Mermaid + PlantUML 交叉，全局到细节 |
| **[VERSIONS.md](./VERSIONS.md)** | 多版本索引 |
| **[versions/2026-06-15/](./versions/2026-06-15/)** | 2026-06-15 冻结快照 |

## 当前版本

- 文档：**v2026.06.15** · 代码：`dev@5d0f866` · `opencode@1.17.7`
- PlantUML 独立源文件：[`diagram/`](./diagram/)

## 文档结构概要

1. **鸟瞰** — 心智模型、C4 上下文、Monorepo 包拓扑  
2. **结构** — 七层模型、HTTP 双路由树  
3. **深潜** — V1/V2 双栈、Coordinator 状态机、Provider Turn、EventV2  
4. **机制** — Location、Tools/Permission、Subagent、Context Epoch、Compaction  

`diagram/` 为可单独渲染的 `.puml` / `.mermaid` 源文件。
