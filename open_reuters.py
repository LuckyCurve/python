"""
打开 Reuters 股票基本面页面
根据 Ticker 自动判断并打开有效的 URL（Nasdaq.O 或 NYSE.N）
"""

import argparse
import subprocess


def build_url(ticker: str, suffix: str) -> str:
    """构建 Reuters 估值页面 URL"""
    return f"https://www.reuters.com/markets/companies/{ticker}{suffix}/key-metrics/valuation"


def open_url(url: str) -> None:
    """使用系统命令打开 URL"""
    subprocess.run(["start", url], shell=True)


def main():
    parser = argparse.ArgumentParser(
        description="打开 Reuters 股票基本面页面",
        epilog="示例: python open_reuters.py PDD",
    )
    parser.add_argument(
        "ticker",
        type=str,
        help="股票代码，如 AAPL、PDD、MSFT",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        type=str,
        choices=[".O", ".N"],
        help="指定后缀：.O(Nasdaq) 或 .N(NYSE)，留空则打开两个链接",
    )
    args = parser.parse_args()

    ticker = args.ticker.upper()

    if args.suffix:
        url = build_url(ticker, args.suffix)
        print(url)
        open_url(url)
    else:
        url_o = build_url(ticker, ".O")
        url_n = build_url(ticker, ".N")
        print(url_o)
        print(url_n)
        open_url(url_o)
        open_url(url_n)


if __name__ == "__main__":
    main()
