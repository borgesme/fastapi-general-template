# research-note-wrap

<p align="center">
    <a href="https://linux.do" alt="LINUX DO"><img src="https://shorturl.at/ggSqS" /></a>
</p>

[![License](https://img.shields.io/github/license/leonsong09/research-note-wrap)](https://github.com/leonsong09/research-note-wrap/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/leonsong09/research-note-wrap)](https://github.com/leonsong09/research-note-wrap/commits/main)
[![Repo Size](https://img.shields.io/github/repo-size/leonsong09/research-note-wrap)](https://github.com/leonsong09/research-note-wrap)

> 把调研/分析会话整理成可复用的 Markdown 结论笔记，优先输出问题对比、判断依据与关键结论。

## 适用场景

当用户想要：
- 总结调研
- 输出结论
- 总结分析
- 输出笔记
- 调研纪要 / 分析纪要
- 总结今天会话里某个主题的分析

## 不适用场景

以下情况更适合其他 skill：
- 当前编码会话收尾：`session-wrap`
- 只看提交生成日报：`commit-daily-summary`
- 按项目汇总当天 Codex 工作：`project-daily-summary`

## 触发词

中文：
- 总结调研
- 输出结论
- 总结分析
- 输出笔记
- 调研纪要
- 分析纪要

English:
- summarize the research
- write the conclusions
- output a note

## 工作流

1. 先判断范围：默认当前会话；若用户说“今天关于 xx 的会话”，则扩到同日相关会话。
2. 先压缩出**主要问题**，优先用表格而不是流水账。
3. 再整理**关键结论**与判断依据。
4. 如需落盘，优先遵循项目 `AGENTS.md` 中定义的输出目录。
5. 若引用代码位点，必须说明其逻辑、作用，以及它如何支撑当前结论。

## 安装

将整个目录复制到本地技能目录，例如：

```text
~/.codex/skills/research-note-wrap
```

或：

```text
~/.agents/skills/research-note-wrap
```

## 仓库结构

```text
research-note-wrap/
  SKILL.md
  README.md
  LICENSE
  .gitignore
  agents/
```

## 配置

公开版不内置任何私人笔记目录。

推荐做法：
- 在项目 `AGENTS.md` 中声明调研笔记默认输出目录；或
- 首次使用时询问用户输出位置。

## 用法示例

### 示例输入

```text
总结调研
```

### 预期行为

- 先抽取核心问题
- 优先使用对比表
- 先确认问题/结论框架，再落 Markdown
- 不输出冗长过程记录

## 输出示例

```markdown
## 问题对比表
| 问题 | 现象/信号 | 核心判断 | 当前结论 | 影响 |
|---|---|---|---|---|
| A | ... | ... | ... | ... |

## 结论对比表
| 结论项 | 依据 | 结论 | 置信度 | 备注 |
|---|---|---|---|---|
| A | ... | ... | 高 | ... |

## 关键结论
- ...
```

## 限制

- 它不能替代真实调研，只负责把已有调研压缩成可读结论。
- 如果跨会话证据不足，仍应明确说明不确定性。
- 若用户需要长期主题研究，而非当天/当前会话总结，需要额外明确范围。

## License

MIT


