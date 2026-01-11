"""
打开 Reuters 股票基本面页面
根据 Ticker 同时打开 Nasdaq(.O) 和 NYSE(.N) 两个版本的页面
"""

import argparse
import subprocess
import sys


def build_url(ticker: str, suffix: str) -> str:
    """构建 Reuters 估值页面 URL"""
    return f"https://www.reuters.com/markets/companies/{ticker}{suffix}/key-metrics/valuation"


def open_url(url: str) -> bool:
    """使用系统命令打开 URL"""
    try:
        subprocess.run(
            ["start", url],
            shell=True,
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"打开失败: {e}", file=sys.stderr)
        return False


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
        help="指定后缀：.O(Nasdaq) 或 .N(NYSE)，留空则同时打开两个",
    )
    args = parser.parse_args()

    ticker = args.ticker.upper()

    if args.suffix:
        url = build_url(ticker, args.suffix)
        print(f"打开: {url}")
        open_url(url)
    else:
        url_o = build_url(ticker, ".O")
        url_n = build_url(ticker, ".N")
        print(f"打开 Nasdaq 版本: {url_o}")
        print(f"打开 NYSE 版本: {url_n}")
        open_url(url_o)
        open_url(url_n)
        print("请手动关闭无效的页面")


if __name__ == "__main__":
    main()
