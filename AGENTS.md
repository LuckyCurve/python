# AGENTS

本目录包含可独立运行的 Python 脚本。依赖通过项目根目录的 `pyproject.toml` 统一管理。

---

## 常用命令

```bash
# 安装/更新依赖
uv sync

# 运行脚本
uv run script_name.py <args>

# 运行所有脚本（测试）
uv run pytest

# 运行单个测试
uv run pytest tests/test_file.py::test_function

# 代码格式化
uv run ruff format .

# 代码检查
uv run ruff check .
```

---

## 代码规范

### 导入顺序
标准库 → 第三方库 → 本地模块。分组间空一行。

```python
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from alpha_vantage.fundamentaldata import FundamentalData
```

### 命名约定
- 函数/变量：`snake_case`
- 类：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`
- 私有成员：前缀 `_`

### 类型标注
使用类型注解，返回类型必须标注。

```python
def build_url(ticker: str, suffix: str) -> str:
    ...
```

### 错误处理
- 使用具体异常类型
- 向上传递时用 `RuntimeError` 包装
- 避免空 except 块

```python
try:
    ...
except ValueError as e:
    raise RuntimeError(f"Failed to get data: {e}")
```

### 脚本结构
```python
"""简短描述"""

import argparse
# imports...

def helper_function() -> ...:
    ...

def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument(...)
    args = parser.parse_args()
    ...

if __name__ == "__main__":
    main()
```

### 关键约定
- 使用 `Path` 处理文件路径
- 使用 `argparse` 提供 CLI 参数
- 环境变量作为后备配置
- 不手动修改 `pyproject.toml`，使用 `uv add`

---

## 脚本列表

### generate_value_investment_analysis.py
从 Alpha Vantage 获取公司财务报表，生成价值投资分析 Prompt。
```bash
uv run generate_value_investment_analysis.py AAPL
```

### get_sec_filings.py
从 SEC EDGAR 获取公司财报 URL。
```bash
uv run get_sec_filings.py AAPL
```

### open_reuters.py
打开 Reuters 股票基本面估值页面，自动判断并只打开有效 URL。
```bash
uv run open_reuters.py PDD
```

### tab_to_column.py
监听剪贴板变化，自动将制表符分隔的数据转换为每行一个数值的格式（自动去除千位分隔符）并复制回剪贴板。使用 Windows API 的系统回调机制，无轮询，低 CPU 占用。
```bash
uv run tab_to_column.py
```

---

## 添加新脚本

1. 使用 `uv add package-name` 添加依赖
2. 遵循上述脚本结构
3. 在 AGENTS.md 脚本列表部分添加文档

---

## 配置

### Alpha Vantage
- `ALPHA_VANTAGE_API_KEY` 环境变量，或使用 `-k` 参数
- 获取 API Key: https://www.alphavantage.co/support/#api-key

### SEC EDGAR
- `SEC_IDENTITY_EMAIL` 环境变量，或使用 `-e` 参数（首次使用需要设置）
