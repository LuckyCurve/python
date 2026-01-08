# AGENTS

本目录包含可独立运行的 Python 脚本，支持通过 `uv run https://xxx.py` 方式直接执行。

每个脚本都遵循 PEP 规范，包含完整的依赖声明（通过 `# /// pyproject` 格式）。

---

## 项目初始化

首次克隆项目后，需要初始化环境并安装依赖：

```bash
# 初始化项目（如果不存在 pyproject.toml）
uv init . --name value-investment-analysis

# 添加依赖
uv add pandas requests alpha-vantage
```

---

## 脚本列表

### generate_value_investment_analysis.py

从 Alpha Vantage 获取公司三大财务报表，生成深度价值投资分析 Prompt 文档。

**功能特性：**
- 获取公司三大财务报表（年报）
- 将数据嵌入深度价值投资分析框架
- 输出到 `analysis_outputs/{TICKER}_analysis_prompt.md`
- 支持 API Key 参数或环境变量

**运行方式：**

```bash
# 本地运行
uv run generate_value_investment_analysis.py AAPL

# 指定 API Key
uv run generate_value_investment_analysis.py AAPL -k YOUR_API_KEY

# 远程运行
uv run https://raw.githubusercontent.com/username/repo/main/generate_value_investment_analysis.py AAPL
```

**脚本内依赖声明（用于远程 URL 运行）：**
```python
# /// pyproject
# Requires: pandas>=1.5.0
# Requires: requests>=2.28.0
# Requires: alpha-vantage>=3.2.0
# ///
```

**环境变量：**
- `ALPHA_VANTAGE_API_KEY` - Alpha Vantage API Key

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

# /// pyproject
# Requires: pandas>=1.5.0
# Requires: requests>=2.28.0
# ///

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
