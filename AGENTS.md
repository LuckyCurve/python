# AGENTS

本目录包含可独立运行的 Python 脚本。

依赖通过项目根目录的 `pyproject.toml` 统一管理。

---

## 项目初始化

首次克隆项目后，需要初始化环境并安装依赖：

```bash
# 初始化项目（如果不存在 pyproject.toml）
uv init . --name value-investment-analysis

# 添加依赖
uv add pandas requests alpha-vantage edgartools
```

---

## 脚本列表

### generate_value_investment_analysis.py

从 Alpha Vantage 获取公司财务报表和 Company Overview，生成深度价值投资分析 Prompt 文档。

**功能特性：**
- 获取 Company Overview（完整字段：股息、账面价值、EV 倍数等）
- 获取公司三大财务报表（年报，不截断，返回所有数据）
- 将数据嵌入专业深度价值投资分析框架（NCAV、Sloan Ratio、Owner Earnings）
- 输出到 `analysis_outputs/{TICKER}_analysis_prompt.md`
- 支持 API Key 参数或环境变量

**运行方式：**

```bash
# 本地运行
uv run generate_value_investment_analysis.py AAPL

# 指定 API Key
uv run generate_value_investment_analysis.py AAPL -k YOUR_API_KEY
```

**环境变量：**
- `ALPHA_VANTAGE_API_KEY` - Alpha Vantage API Key

---

### get_sec_filings.py

从 SEC EDGAR 获取公司财报 URL 地址。

**功能特性：**
- 自动识别公司类型（美国公司 vs 外国公司 ADR）
- 获取 10-K/20-F 年报和 10-Q/6-K 季报
- 支持按年份筛选
- 支持 JSON 格式输出

**运行方式：**

```bash
# 基本用法
uv run get_sec_filings.py AAPL

# 指定年份
uv run get_sec_filings.py AAPL -y 3

# JSON 格式输出
uv run get_sec_filings.py AAPL --json

# 指定身份邮箱（首次使用需要）
uv run get_sec_filings.py AAPL -e your-email@example.com
```

**环境变量：**
- `SEC_IDENTITY_EMAIL` - SEC 要求的身份标识邮箱

---

## 添加新脚本指南

新增脚本时请遵循以下规范：

### 1. 项目初始化

首次设置项目：
```bash
uv init . --name value-investment-analysis
```

### 2. 添加依赖

**重要：不要手动修改 pyproject.toml，使用 uv 命令管理依赖。**

当脚本需要新依赖时：
```bash
uv add package-name
```

### 3. 脚本结构

```python
"""脚本简短描述（1-2行）"""

import argparse
# 其他 imports...

def main():
    """主函数逻辑"""
    ...

if __name__ == "__main__":
    main()
```

### 4. 文档要求

- 使用 `argparse` 提供命令行参数
- 包含 `--help` 说明
- 添加使用示例

### 5. 更新 AGENTS.md

在 AGENTS.md 中添加新脚本的文档。
