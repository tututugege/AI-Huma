# `docs/exp/` — 单实验独立报告目录（EXP-068+）

从 `EXP-068` 起，每次架构/性能探索单独建一个文件 `EXP-<编号>-<简称>.md`，并在 [../EXPLORATION.md](../EXPLORATION.md) 顶部索引表追加一行链接（`EXP-001 ~ EXP-067` 正文已归档至 [../archive/EXPLORATION_001_067.md](../archive/EXPLORATION_001_067.md)）。

## 精简模板

```markdown
# EXP-XXX <题目>

- **日期 / 分支 / 状态**：YYYY-MM-DD；`<repo> exp/<name>`；探索中 / 已合入 / 不采纳
- **开关与默认关闭回归**：`<开关>=0` 时 gate 周期不变
- **问题与方法**：...
- **模型近似与硬件代价**：...
- **结果表**：...
- **结论与后续**：...
```
