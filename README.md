# scraping-to-analysis

Python 数据采集与分析学习项目：使用 Scrapling 采集数据、pandas 清洗统计、Matplotlib 绘制图表。

## 项目内容

- `scrape_quotes.py`：采集名言练习站，自动翻页并保存 `all_quotes.csv`。
- `analyze_laptops.py`：读取 50 条笔记本电脑样本，检查价格、填充价格说明、标记同名商品，生成统计表和图表。
- `taobao_laptops_50.csv`：分析使用的原始样本，来自手动提供的商品列表 HTML，经 Scrapling 离线提取；本项目未提供自动访问淘宝的脚本。
- `taobao_laptops_50_detail_links.csv`：保留原链接，并根据商品 ID 整理标准详情网址；没有联网验证最终跳转。
- `analysis_output/`：脚本生成的清洗数据、价格统计和三张图。
- 其他 CSV、TXT 和 PNG 文件：学习过程中保存的练习结果。

## 安装

以下命令在项目目录的 PowerShell 中运行。依赖版本来自本项目已验证的 Python 3.11 环境。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

无需激活虚拟环境。当前两个脚本均不需要浏览器；如另外使用 Scrapling 浏览器抓取功能，再运行 `.\.venv\Scripts\scrapling.exe install`。

## 运行

### 交互式商品看板

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\dashboard.py
```

在浏览器打开终端显示的本机地址（通常为 http://127.0.0.1:8501）。看板提供关键词、价格范围、价格说明和同名标记筛选，指标与图表同步更新；明细支持价格排序、打开商品链接和导出当前结果。点击「重置筛选」恢复全部商品。空结果会提供调整提示。

看板只读取本地样本，不自动访问淘宝、不更新商品价格。修改 CSV 后刷新页面即可读取新数据。服务仅监听本机，按 `Ctrl+C` 停止。也可在 PowerShell 运行 `./start_dashboard.ps1`。

运行数据与页面测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

采集练习站名言（需要网络）：

```powershell
.\.venv\Scripts\python.exe .\scrape_quotes.py
```

分析本地商品数据（无需联网）：

```powershell
.\.venv\Scripts\python.exe .\analyze_laptops.py
```

分析结果保存在脚本所在目录的 `analysis_output` 文件夹。输入 CSV 支持 UTF-8 和 GB18030（兼容中文 Windows/Excel 导出的 CSV），输出统一使用带 BOM 的 UTF-8。重复运行会更新输出，无需关闭图表弹窗；在 Excel 中打开的输出文件需先关闭，避免占用。

## 分析示例

当前样本共 50 条，平均展示价格约 5161.35 元，中位数为 4063.50 元。两条同名记录仅标记待核查，未删除。

![商品价格区间分布](analysis_output/price_bar.png)

![价格分布与统计参考线](analysis_output/price_hist_stats.png)

统计仅描述当前搜索样本的页面展示价格，不代表销量或整体市场。商品可能包含不同配置、优惠和补贴条件，不能仅凭标题推断配置，也不能把不同条件下的价格直接当作同款比较。

采集练习请控制请求频率，遵守目标网站的访问规则。样本价格和链接可能随时间变化。
# 看板直接读取 MySQL

先运行 `init_database.sql` 中的建表和清洗视图语句，并导入商品数据。
安装项目依赖后，将 `.streamlit/secrets.example.toml` 复制为
`.streamlit/secrets.toml`，在本机填写 MySQL 用户和密码。
真实配置文件已在 `.gitignore` 中排除，不要上传密码。

启动方式仍为：

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\dashboard.py
```

存在 `[mysql]` 配置时，看板直接查询 `cleaned_product_snapshots` 视图。
每次页面重新运行或点击“刷新数据”都会重新查询，不读取导出的 CSV。
连接失败时显示错误，不自动改用旧 CSV。未配置 MySQL 时保留原来的 CSV 模式。
本机练习可使用现有账号；部署时应改用仅有该视图查询权限的账号。
