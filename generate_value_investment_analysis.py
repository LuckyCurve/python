"""
从 Alpha Vantage 获取公司三大财务报表（资产负债表、利润表、现金流量表）
输出原始完整数据，方便复制给 AI 分析
"""

import argparse
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from alpha_vantage.fundamentaldata import FundamentalData

OUTPUT_DIR = Path(__file__).parent / "analysis_outputs"

PROMPT_TEMPLATE = """# Role
你是一位拥有20年经验的**深度价值投资者（Deep Value Investor）**，你的投资哲学深受本杰明·格雷厄姆（Benjamin Graham）和霍华德·马克斯（Howard Marks）的影响。
你的核心原则是：**首要任务是避免本金永久性损失，其次才是追求回报。** 你对财报数据持怀疑态度，倾向于从最坏的情况（Downside Scenario）进行分析。

# Task
我将为你提供一家公司的财务数据（包括市场数据、资产负债表、利润表、现金流量表）。请根据这些数据进行严格的基本面分析。

# Context (Data Placeholder)
{data}

# Analysis Framework (Step-by-Step)

## 1. 深度价值计算 (The "Naked" Numbers)
请务必计算并展示以下指标，用于剥去会计粉饰：
* **安全边际 (Margin of Safety)**：计算 NCAV (净流动资产价值 = 流动资产 - 总负债)。当前市值是 NCAV 的几倍？
* **调整后 FCF (Real FCF)**：`Operating Cashflow` - `Capital Expenditures` - `Stock-Based Compensation` (若数据未列出，请根据 Operating Expenses 的异常变动做出风险提示)。
* **所有者收益 (Owner Earnings)**：净利润 + 折旧摊销 - 必要资本支出 - 营运资本变动。
* **资本回报率 (ROIC)**：EBIT / (净股权 + 净债务)。判断其护城河是"真金"还是"烧钱"。

## 2. 资产负债表"排雷" (Stress Test)
* **清算价值分析**：如果公司业务停滞，其现金及短投能否覆盖所有债务？检查 `Other Current Assets` 占比，若过高，需质疑其资产真实性。
* **负营运资本风险**：观察 `Accounts Payable` 和 `Other Current Liabilities`。公司是否过度依赖占用供应商资金来维持运营？在增长放缓时，这是否会触发流动性挤兑？
* **无形资产剔除**：将 `Goodwill` 和 `Intangible Assets` 直接从净资产中扣除，计算"有形净资产 (Tangible Book Value)"。

## 3. 盈利含金量穿透 (Quality Over Quantity)
* **权责发生制检查**：计算 Sloan Ratio (应计比率)。如果 (净利润 - 现金流) / 总资产比例过高，警告可能存在会计操纵。
* **利润率边界测试**：当前毛利率/营业利润率处于历史什么位置？要求模拟当竞争加剧、利润率收缩 30% 时，公司是否还会亏损。
* **稀释效应**：不看 EPS，看总股本变动。如果公司在回购，计算回购注销比例；如果在增发，计算稀释率。

## 4. 极端保守评分模型 (0-100分)
* **资产安全 (40分)**：净现金状态、清算价值保障、资产负债表真实度。
* **现金机器 (30分)**：FCF 连续性、对 SBC 的依赖度、资本开支效率。
* **估值边际 (20分)**：当前价格相对于 Intrinsic Value (内在价值) 的折扣（要求至少 30% 折扣才能给高分）。
* **管理层行为 (10分)**：是否存在破坏股东价值的收购或过度激励。

## 5. 最终审判 (Investment Conclusion)
* **评级**：**强力买入 / 买入 / 观望 / 卖出**。
* **格雷厄姆式评价**：这是一家"烟蒂股"吗？还是一家以合理价格交易的卓越公司？
* **毁灭性情景 (Kill the Business)**：列出三种能让这家公司在 3 年内破产或市值腰斩的外部/内部诱因。
* **一句话冷评**：用一句刻薄但深刻的话，戳穿该公司的财务幻象或商业本质。

# Output Style
*   使用 Markdown 表格展示计算出的关键指标。
*   语气客观、冷静、甚至带有批判性。不要使用"令人兴奋"、"潜力巨大"等营销词汇。
"""


def format_number(value: Any) -> str:
    if value is None or value == "None" or value == "" or pd.isna(value):
        return "-"
    try:
        num = float(value)
        abs_num = abs(num)
        sign = "-" if num < 0 else ""
        if abs_num >= 1e9:
            return f"{sign}{abs_num / 1e9:.2f}B"
        elif abs_num >= 1e6:
            return f"{sign}{abs_num / 1e6:.2f}M"
        elif abs_num >= 1e3:
            return f"{sign}{abs_num / 1e3:.2f}K"
        elif abs_num == 0:
            return "0"
        else:
            return f"{num:.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_table(title: str, df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return f"\n## {title}\n无数据\n"

    df = df

    if "fiscalDateEnding" in df.columns:
        dates = df["fiscalDateEnding"].tolist()
    else:
        dates = [f"Period {i + 1}" for i in range(len(df))]

    lines = [f"\n## {title}", ""]
    header = "| Field | " + " | ".join(dates) + " |"
    separator = "|" + "---|" * (len(dates) + 1)
    lines.extend([header, separator])

    skip_fields = {"fiscalDateEnding", "reportedCurrency"}

    for col in df.columns:
        if col in skip_fields:
            continue
        row_values = [format_number(v) for v in df[col].tolist()]
        row = f"| {col} | " + " | ".join(row_values) + " |"
        lines.append(row)

    return "\n".join(lines)


def check_api_error(data: dict) -> None:
    """检查 Alpha Vantage 返回的数据是否包含错误信息"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and "Thank you for using Alpha Vantage" in value:
                raise RuntimeError(f"API Error: {value}")
            if isinstance(value, str) and "API rate limit" in value:
                raise RuntimeError(f"API Rate Limit: {value}")


def get_stock_quote(ticker: str, api_key: str) -> dict:
    result = {
        "price": None,
        "change": None,
        "change_percent": None,
        "overview": None,
    }

    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        check_api_error(data)

        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            result["price"] = quote.get("05. price")
            result["change"] = quote.get("09. change")
            result["change_percent"] = quote.get("10. change percent")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to get quote: {e}")

    time.sleep(1)

    try:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        check_api_error(data)

        if data and "Symbol" in data:
            result["overview"] = data
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to get company overview: {e}")

    return result


def format_market_info(quote_data: dict) -> str:
    lines = ["## Company Overview", ""]

    if quote_data.get("price"):
        price = float(quote_data["price"])
        lines.append(f"| Current Price | ${price:.2f} |")
    else:
        lines.append("| Current Price | - |")

    if quote_data.get("change") and quote_data.get("change_percent"):
        change = float(quote_data["change"])
        change_pct = quote_data["change_percent"]
        sign = "+" if change >= 0 else ""
        lines.append(f"| Change | {sign}{change:.2f} ({change_pct}) |")

    lines.append("")

    overview = quote_data.get("overview")
    if overview:
        overview_lines = []

        for key, value in overview.items():
            if value and value != "None" and str(value).strip():
                if isinstance(value, (int, float)):
                    if abs(value) >= 1e9:
                        formatted = f"{value / 1e9:.2f}B"
                    elif abs(value) >= 1e6:
                        formatted = f"{value / 1e6:.2f}M"
                    elif abs(value) >= 1e3:
                        formatted = f"{value / 1e3:.2f}K"
                    else:
                        formatted = f"{value:.2f}"
                    overview_lines.append(f"| {key} | {formatted} |")
                else:
                    overview_lines.append(f"| {key} | {value} |")

        if overview_lines:
            lines.append("| Metric | Value |")
            lines.append("|---|--- |")
            lines.extend(overview_lines)

    lines.append("")
    return "\n".join(lines)


def get_financials(ticker: str, api_key: str) -> str:
    fd = FundamentalData(key=api_key, output_format="json")

    output_lines = [f"# {ticker} Financial Statements (Annual)", ""]

    print(f"Fetching {ticker} Market Data...")
    quote_data = get_stock_quote(ticker, api_key)
    output_lines.append(format_market_info(quote_data))
    output_lines.append("")

    print(f"Fetching {ticker} Balance Sheet...")
    balance_df, _ = fd.get_balance_sheet_annual(ticker)
    check_api_error(balance_df)
    output_lines.append(format_table("Balance Sheet", balance_df))
    time.sleep(1)

    print(f"Fetching {ticker} Income Statement...")
    income_df, _ = fd.get_income_statement_annual(ticker)
    check_api_error(income_df)
    output_lines.append(format_table("Income Statement", income_df))
    time.sleep(1)

    print(f"Fetching {ticker} Cash Flow Statement...")
    cashflow_df, _ = fd.get_cash_flow_annual(ticker)
    check_api_error(cashflow_df)
    output_lines.append(format_table("Cash Flow Statement", cashflow_df))

    return "\n".join(output_lines)


def generate_analysis_prompt(ticker: str, financial_data: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{ticker}_analysis_prompt.md"
    prompt = PROMPT_TEMPLATE.replace("{data}", financial_data)
    output_path.write_text(prompt, encoding="utf-8")
    print(f"已生成分析文档: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="从 Alpha Vantage 获取公司三大财务报表（年报）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  uv run generate_value_investment_analysis.py AAPL\n  uv run generate_value_investment_analysis.py MSFT -k YOUR_API_KEY",
    )
    parser.add_argument("ticker", type=str, help="股票代码，如 AAPL, MSFT, GOOGL")
    parser.add_argument(
        "-k", "--api-key", type=str, default=None, help="Alpha Vantage API Key"
    )

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("错误: 请提供 Alpha Vantage API Key")
        print(
            "方式1: -k 参数: uv run generate_value_investment_analysis.py AAPL -k YOUR_API_KEY"
        )
        print("方式2: 环境变量: set ALPHA_VANTAGE_API_KEY=YOUR_API_KEY")
        print("\n获取 API Key: https://www.alphavantage.co/support/#api-key")
        return

    ticker = args.ticker.upper()
    output_path = OUTPUT_DIR / f"{ticker}_analysis_prompt.md"

    if output_path.exists():
        print(f"文件已存在: {output_path}")
        print("如需重新生成，请先删除该文件。")
        return

    try:
        financial_data = get_financials(ticker, api_key)
        generate_analysis_prompt(ticker, financial_data)
    except RuntimeError as e:
        print(f"\n错误: {e}")
        print("\n请稍后重试，或升级 Alpha Vantage 订阅计划。")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
