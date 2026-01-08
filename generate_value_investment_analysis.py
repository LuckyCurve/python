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

## 1. 数据清洗与关键指标计算
由于数据可能未直接提供比率，请务必先计算以下指标：
*   **市值 (Market Cap)**：使用 `Current Price` * `CommonStockSharesOutstanding` (最新一期)。
*   **企业价值 (EV)**：市值 + 总债务 - 现金及现金等价物。
*   **估值倍数**：P/E (市盈率), P/OCF (市现率), P/B (市净率)。
*   **自由现金流 (FCF)**：`Operating Cash Flow` - `Capital Expenditures`。
*   **ROIC (资本回报率)**：估算即可，用于判断公司配置资本的效率。

## 2. 资产负债表压力测试 (最重要的环节)
*   **偿债能力**：计算"净债务/EBITDA"和"流动比率"。公司是否有迫在眉睫的偿债危机？
*   **资产质量**：检查 `Goodwill` (商誉) 和 `Intangible Assets` (无形资产) 在总资产中的占比。如果占比过高，请视为风险（由收购驱动的增长且资产虚高）。
*   **现金储备**：公司的现金能否覆盖短期债务？

## 3. 盈利质量与现金流验证
*   **利润含金量**：严格对比 `Net Income` (净利润) 和 `Operating Cashflow` (经营现金流)。如果净利润很高但现金流很差，请发出"高风险"红色警报（可能是激进的会计确认）。
*   **趋势分析**：观察过去几年的 `Gross Margin` (毛利率) 和 `Operating Margin` (营业利润率)。是在提升、持平还是恶化？
*   **股东稀释**：检查 `CommonStockSharesOutstanding` 过去几年的变化。公司是在回购股票（利好）还是在增发股票稀释股东（利空）？

## 4. 保守派评分模型 (0-100分)
请根据以下严格标准打分，如果不确定，宁可打低分：

*   **财务健康 (40分)**：
    *   满分标准：净现金状态（现金>债务），流动比率>2。
    *   扣分项：高杠杆、存货积压、商誉过高。
*   **盈利稳定性 (30分)**：
    *   满分标准：毛利率稳定，FCF（自由现金流）连续多年为正且覆盖股息。
    *   扣分项：盈利波动剧烈、经营现金流持续低于净利润。
*   **估值吸引力 (20分)**：
    *   满分标准：P/E 或 P/FCF 显著低于历史平均或行业常识（例如 P/E < 15，除非是高增长行业可适当放宽但仍需保守）。
*   **股东回报 (10分)**：
    *   满分标准：持续的分红或实质性的股票回购。

## 5. 投资结论
*   **评级**：**强力买入 / 买入 / 观望 / 卖出**。
    *   *注意：除非这是一家极度被低估且极其安全的公司，否则不要轻易给"买入"。大多数平庸的公司应评为"观望"。*
*   **下行风险 (Downside Risks)**：请列出如果是最坏情况，投资者可能会因为什么亏钱？（例如：债务违约、利润率均值回归、过度资本开支）。
*   **一句话总结**：用犀利、不留情面的语言总结这家公司的现状。

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

    df = df.head(4)

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
        "market_cap": None,
        "pe_ratio": None,
        "52_week_high": None,
        "52_week_low": None,
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

        if data and "MarketCapitalization" in data:
            result["market_cap"] = data.get("MarketCapitalization")
            result["pe_ratio"] = data.get("PERatio")
            result["52_week_high"] = data.get("52WeekHigh")
            result["52_week_low"] = data.get("52WeekLow")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to get company overview: {e}")

    return result


def format_market_info(quote_data: dict) -> str:
    lines = ["## Market Data (Latest)", ""]
    lines.append("| Metric | Value |")
    lines.append("|---|---|")

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

    if quote_data.get("market_cap"):
        market_cap = float(quote_data["market_cap"])
        lines.append(f"| Market Cap | {format_number(market_cap)} |")
    else:
        lines.append("| Market Cap | - |")

    if quote_data.get("pe_ratio") and quote_data["pe_ratio"] != "None":
        lines.append(f"| P/E Ratio | {quote_data['pe_ratio']} |")

    if quote_data.get("52_week_high") and quote_data.get("52_week_low"):
        high = float(quote_data["52_week_high"])
        low = float(quote_data["52_week_low"])
        lines.append(f"| 52-Week High | ${high:.2f} |")
        lines.append(f"| 52-Week Low | ${low:.2f} |")

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
