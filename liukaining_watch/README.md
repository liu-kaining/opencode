# liukaining_watch

OpenCode 项目架构图解与版本快照。

## 入口

| 文件 | 说明 |
|------|------|
| **[OpenCode架构图解.md](./OpenCode架构图解.md)** | 主文档：PlantUML + **Kroki 渲染图片** |
| **[VERSIONS.md](./VERSIONS.md)** | 多版本索引 |
| **[versions/2026-06-15/](./versions/2026-06-15/)** | 2026-06-15 快照 |

## Kroki 图片渲染

图表通过自托管 Kroki 转为 SVG，直接嵌入 Markdown：

```
https://kroki.thetamind.ai/plantuml/svg/{encoded}
```

修改 PlantUML 源码后重新生成图片链接：

```bash
python3 liukaining_watch/scripts/embed-kroki-images.py
```

## 当前版本

- 文档：**v2026.06.15** · 代码：`dev@5305247f0` · `opencode@1.17.7`
- Kroki：**https://kroki.thetamind.ai/**

## 文档结构

鸟瞰 → 结构 → 双栈 → 深潜（V1/V2/Coordinator/Turn）→ 机制（Event/Location/Tools/Subagent）→ 专题（Epoch/Compaction/Agent）

独立 `.puml` 见 [`diagram/`](./diagram/)。
