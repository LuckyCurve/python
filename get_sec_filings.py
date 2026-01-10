"""
获取公司 SEC 财报的 URL 地址
使用 edgartools 库从 SEC EDGAR 获取数据
支持 10-K（年报）、10-Q（季报）以及对应的外国公司表格
"""

import argparse
import json
import os

from edgar import Company, set_identity


def get_sec_filings(ticker: str, years: int = 5) -> dict[str, list[dict]]:
    """
    获取指定公司年度财报（10-K/20-F）和季度财报（10-Q/6-K）的 URL 地址

    Args:
        ticker: 股票代码，如 AAPL, MSFT, BABA
        years: 获取最近几年的报告，默认 5 年

    Returns:
        包含两类财报信息的字典:
        - annual: 年报列表 (10-K 或 20-F)
        - quarterly: 季报列表 (10-Q 或 6-K)

        每个财报字典包含:
        - ticker: 股票代码
        - form_type: 表格类型
        - filing_date: 提交日期
        - report_date: 报告期截止日期
        - document_url: 文档直接链接
        - homepage_url: SEC 索引页面

    Note:
        美国公司: 10-K（年报）、10-Q（季报）
        外国公司（ADR）: 20-F（年报）、6-K（季度/半年报）
    """
    company = Company(ticker)
    print(f"正在获取 {company.name} ({ticker}) 的财报 URL...")

    results = {"annual": [], "quarterly": []}

    # 获取年报: 先尝试 10-K，如果没有则尝试 20-F
    annual_filings, annual_form = _get_filings(company, "10-K", "20-F", years)
    if annual_filings:
        print(f"找到 {len(annual_filings)} 份 {annual_form} 年报")
        results["annual"] = _process_filings(annual_filings, ticker, annual_form)
    else:
        print(f"未找到 {ticker} 的 10-K 或 20-F 年报")

    # 获取季报: 先尝试 10-Q，如果没有则尝试 6-K
    # 季报数量通常是年报的 3-4 倍
    quarterly_count = years * 4
    quarterly_filings, quarterly_form = _get_filings(
        company, "10-Q", "6-K", quarterly_count
    )
    if quarterly_filings:
        print(f"找到 {len(quarterly_filings)} 份 {quarterly_form} 季报")
        results["quarterly"] = _process_filings(
            quarterly_filings, ticker, quarterly_form
        )
    else:
        print(f"未找到 {ticker} 的 10-Q 或 6-K 季报")

    return results


def _get_filings(company: Company, primary_form: str, fallback_form: str, count: int):
    """
    尝试获取指定类型的财报，如果没有则尝试备选类型

    Args:
        company: Company 对象
        primary_form: 首选表格类型
        fallback_form: 备选表格类型
        count: 获取数量

    Returns:
        (filings, form_type) 元组
    """
    filings = company.get_filings(form=primary_form).latest(count)
    if filings:
        return filings, primary_form

    print(f"未找到 {primary_form}，尝试获取 {fallback_form}...")
    filings = company.get_filings(form=fallback_form).latest(count)
    if filings:
        return filings, fallback_form

    return None, None


def _process_filings(filings, ticker: str, form_type: str) -> list[dict]:
    """
    处理财报列表，提取关键信息

    Args:
        filings: 财报列表
        ticker: 股票代码
        form_type: 表格类型

    Returns:
        处理后的财报信息列表
    """
    results = []
    for filing in filings:
        document_url = f"{filing.base_dir}/{filing.primary_document}"

        result = {
            "ticker": ticker,
            "form_type": form_type,
            "filing_date": str(filing.filing_date),
            "report_date": str(filing.report_date)
            if hasattr(filing, "report_date")
            else None,
            "document_url": document_url,
            "homepage_url": filing.homepage_url,
        }
        results.append(result)
        print(f"  {form_type} {filing.filing_date}: {document_url}")

    return results


# 保持向后兼容的别名
def get_10k_urls(ticker: str, years: int = 5) -> list[dict]:
    """向后兼容的函数，仅返回年报"""
    return get_sec_filings(ticker, years)["annual"]


def main():
    parser = argparse.ArgumentParser(
        description="获取公司 SEC 财报 URL (10-K/10-Q)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  uv run get_sec_filing_urls.py AAPL\n  uv run get_sec_filing_urls.py AAPL -y 3\n  uv run get_sec_filing_urls.py AAPL --json",
    )
    parser.add_argument("ticker", type=str, help="股票代码，如 AAPL, MSFT, BABA")
    parser.add_argument(
        "-y", "--years", type=int, default=5, help="获取最近几年的报告 (默认: 5)"
    )
    parser.add_argument(
        "-e",
        "--email",
        type=str,
        default=None,
        help="SEC 要求的身份标识邮箱 (或通过 SEC_IDENTITY_EMAIL 环境变量设置)",
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        choices=["all", "annual", "quarterly"],
        default="all",
        help="财报类型: all=全部, annual=年报, quarterly=季报 (默认: all)",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    email = args.email or os.environ.get("SEC_IDENTITY_EMAIL")
    if not email:
        email = "your-email@example.com"
    set_identity(email)

    ticker = args.ticker.upper()
    results = get_sec_filings(ticker, args.years)

    if args.type == "annual":
        output = {"annual": results["annual"]}
    elif args.type == "quarterly":
        output = {"quarterly": results["quarterly"]}
    else:
        output = results

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n=== {ticker} 财报汇总 ===")
        if "annual" in output:
            print(f"年报 (10-K/20-F): {len(output['annual'])} 份")
        if "quarterly" in output:
            print(f"季报 (10-Q/6-K): {len(output['quarterly'])} 份")


if __name__ == "__main__":
    main()
