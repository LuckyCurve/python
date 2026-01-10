# Value Investment Analysis

从 Alpha Vantage 获取公司财务报表，生成深度价值投资分析 Prompt。

## 快速开始

```bash
# 初始化项目
uv init . --name value-investment-analysis

# 安装依赖
uv add pandas requests alpha-vantage

# 生成分析文档
uv run generate_value_investment_analysis.py AAPL
```

## 脚本列表

| 脚本 | 功能 |
|-----|------|
| `generate_value_investment_analysis.py` | 获取财务数据 + Company Overview，生成深度价值投资分析 Prompt |

## 输出

- **分析文档**：`analysis_outputs/{TICKER}_analysis_prompt.md`
- **数据范围**：返回 API 所有可用数据（不截断）
  - Company Overview（股息、账面价值、EV 倍数等完整字段）
  - 资产负债表、利润表、现金流量表（全部年度报告）

## 配置

- `ALPHA_VANTAGE_API_KEY` 环境变量，或使用 `-k` 参数
- 获取 API Key: https://www.alphavantage.co/support/#api-key
