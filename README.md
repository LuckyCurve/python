# Value Investment Analysis

从 Alpha Vantage 获取公司财务报表，生成深度价值投资分析 Prompt。

## 快速开始

```bash
# 初始化项目
uv init . --name value-investment-analysis

# 安装依赖
uv add pandas requests alpha-vantage edgartools curl-cffi

# 生成分析文档
uv run generate_value_investment_analysis.py AAPL

# 获取 SEC 财报 URL
uv run get_sec_filings.py AAPL
```

## 脚本列表

| 脚本 | 功能 |
|-----|------|
| `generate_value_investment_analysis.py` | 获取财务数据 + Company Overview，生成深度价值投资分析 Prompt |
| `get_sec_filings.py` | 从 SEC EDGAR 获取公司财报 URL（10-K/20-F、10-Q/6-K） |
| `open_reuters.py` | 打开 Reuters 股票基本面估值页面（直接输出并打开两个链接） |
| `tab_to_column.py` | 监听剪贴板变化，自动将制表符分隔的数据转换为每行一个数值 |

## 使用示例

```bash
# 生成价值投资分析
uv run generate_value_investment_analysis.py AAPL

# 获取 SEC 财报 URL
uv run get_sec_filings.py AAPL

# 打开 Reuters 估值页面
uv run open_reuters.py PDD

# 剪贴板数据转换
uv run tab_to_column.py
```

## 输出

- **分析文档**：`analysis_outputs/{TICKER}_analysis_prompt.md`
- **数据范围**：返回 API 所有可用数据（不截断）
  - Company Overview（股息、账面价值、EV 倍数等完整字段）
  - 资产负债表、利润表、现金流量表（全部年度报告）

## 配置

### Alpha Vantage
- `ALPHA_VANTAGE_API_KEY` 环境变量，或使用 `-k` 参数
- 获取 API Key: https://www.alphavantage.co/support/#api-key

### SEC EDGAR
- `SEC_IDENTITY_EMAIL` 环境变量，或使用 `-e` 参数（首次使用需要设置）
