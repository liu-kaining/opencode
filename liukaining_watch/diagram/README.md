# diagram 源文件

主文档 **[OpenCode架构图解.md](../OpenCode架构图解.md)** 已 **统一使用 PlantUML**，图表内嵌于 Markdown，建议优先阅读主文档。

本目录保留独立 `.puml` 源文件，便于 IDE 批量渲染或导出 PNG/SVG：

| 文件 | 内容 |
|------|------|
| `http-server-routes.puml` | HTTP 双路由树 |
| `coordinator-fsm.puml` | SessionRunCoordinator 状态机 |
| `v2-provider-turn.puml` | 单次 Provider Turn |
| `12-location-scoped-services.puml` | LocationServiceMap 分层 |
| `01-*.puml` / `*.mermaid` | 早期草稿（主文档已 supersede） |

渲染：PlantUML IDE 插件 / [plantuml.com](https://www.plantuml.com/plantuml)
