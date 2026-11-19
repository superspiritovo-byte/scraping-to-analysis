import csv
from decimal import Decimal
from getpass import getpass
from pathlib import Path

import mysql.connector


# CSV 文件位于脚本所在的项目文件夹中
csv_path = Path(__file__).resolve().parent / "taobao_laptops_50.csv"

# 优先读取 UTF-8；兼容 Excel 保存的 GB18030 编码
try:
    csv_text = csv_path.read_text(encoding="utf-8-sig")
except UnicodeDecodeError:
    csv_text = csv_path.read_text(encoding="gb18030")

# 将 CSV 的四列转换成待插入的数据
records = [
    (
        row["名称"],
        Decimal(row["页面展示价格（元）"]),
        row["价格说明"].strip() or None,
        row["商品链接"],
    )
    for row in csv.DictReader(csv_text.splitlines())
]

if not records:
    raise ValueError("CSV 中没有商品数据，已停止导入。")

# 密码只在运行时输入，不写入代码文件
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
    # 本次练习只允许导入空表，避免重复运行造成重复数据
    cursor.execute("select count(*) from product_snapshots")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"表中已有 {existing_count} 条记录，本次未导入。")
    else:
        # 使用参数传递数据，正确处理名称、链接中的特殊字符
        sql = """
            insert into product_snapshots
                (name, display_price, price_note, detail_url)
            values (%s, %s, %s, %s)
        """

        cursor.executemany(sql, records)
        connection.commit()

        print(f"导入完成：{len(records)} 条商品记录。")

except Exception:
    # 导入失败时，撤销本次尚未提交的数据
    connection.rollback()
    raise

finally:
    cursor.close()
    connection.close()