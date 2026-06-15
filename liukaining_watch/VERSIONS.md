# 架构文档版本索引

OpenCode 迭代很快，每次重大变更应新增一个日期快照，**不要覆盖旧版本**。

## 版本列表

| 日期 | 文档 | 包版本 | Git Commit | 说明 |
|------|------|--------|------------|------|
| **2026-06-15** | [versions/2026-06-15/OpenCode架构图解.md](./versions/2026-06-15/OpenCode架构图解.md) | opencode **1.17.7** | `5d0f866` → `5305247f0` | 审查勘误 + 专家级图解重构（Mermaid/PlantUML） |
| _latest_ | [OpenCode架构图解.md](./OpenCode架构图解.md) | 同左 | 同左 | 始终指向最新审查结果 |

## 如何维护新版本

当 opencode 有重大架构变更（例如 V2 完全替代 V1、Session API 合并）时：

1. 复制当前 `OpenCode架构图解.md` 到 `versions/YYYY-MM-DD/OpenCode架构图解.md`
2. 新建 `versions/YYYY-MM-DD/META.md`，记录 commit、包版本、审查清单、相对上版的变更
3. 更新本文件版本列表
4. 更新 `OpenCode架构图解.md` 顶部的版本 banner

## 建议触发新快照的条件

- `packages/core/src/session/` 或 `packages/opencode/src/session/` 结构性重构
- HTTP API 路由合并或废弃（Instance vs `/api/session`）
- V1 SessionPrompt 被移除或默认切到 V2
- 大版本发布（如 1.18.x → 2.0.x）
