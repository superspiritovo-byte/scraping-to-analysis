from getpass import getpass
from pathlib import Path

import mysql.connector
import pandas as pd


# 运行时输入密码，不写入文件
password = getpass("请输入本机 MySQL 的 root 密码：")

connection = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password=password,
    database="scraping_to_analysis",
    charset="utf8mb4",
)

cursor = connection.cursor()

try:
    # 从清洗视图读取数据，并使用项目原来的中文列名
    cursor.execute("""
        select
            id as 编号,
            name as 名称,
            display_price as `页面展示价格（元）`,
            price_note as 价格说明,
            detail_url as 商品链接
        from cleaned_product_snapshots
        order by id
    """)

    # 获取查询结果和列名，构建 pandas 表格
    records = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    df = pd.DataFrame(records, columns=columns)

finally:
    cursor.close()
    connection.close()

# MySQL 的 decimal 在 Python 中通常为 Decimal，转为数值列便于分析
price_column = "页面展示价格（元）"
df[price_column] = pd.to_numeric(df[price_column], errors="raise")

# 验证读取结果
print(df.head())
print(f"\n读取完成：{len(df)} 条商品")
print(f"平均价格：{df[price_column].mean():.2f} 元")
print(f"未标注价格说明：{df['价格说明'].eq('未标注').sum()} 条")

# 导出一份独立文件，保留原来的 CSV
output_path = Path(__file__).resolve().parent / "laptops_from_mysql.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"已导出：{output_path}")