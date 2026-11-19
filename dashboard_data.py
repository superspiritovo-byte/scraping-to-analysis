"""看板的数据读取和筛选，不依赖页面组件，便于测试与学习。"""

from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import pandas as pd

PRICE = "页面展示价格（元）"
LABELS = ["低于3000", "3000至不足5000", "5000至不足8000", "8000及以上"]


def load_data(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="gb18030")
    return prepare_data(df)


def load_mysql_data(config) -> pd.DataFrame:
    """读取清洗视图；不缓存连接，不向页面暴露连接异常的敏感内容。"""
    import mysql.connector

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=config.get("host", "127.0.0.1"),
            port=int(config.get("port", 3306)),
            user=config["user"], password=config["password"],
            database=config.get("database", "scraping_to_analysis"),
            charset="utf8mb4", connection_timeout=10,
        )
        cursor = connection.cursor()
        cursor.execute("""
            select id, name, display_price, price_note, detail_url
            from cleaned_product_snapshots order by id
        """)
        df = pd.DataFrame(cursor.fetchall(), columns=["编号", "名称", PRICE, "价格说明", "商品链接"])
    except Exception:
        raise ValueError("MySQL 读取失败，请检查本机服务、账号密码及清洗视图是否存在。") from None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
    return prepare_data(df)


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    required = {"名称", PRICE, "价格说明", "商品链接"}
    if not required.issubset(df.columns):
        raise ValueError("缺少必需列：" + "、".join(sorted(required - set(df.columns))))
    if df.empty:
        raise ValueError("数据文件没有商品记录")
    df[PRICE] = pd.to_numeric(df[PRICE], errors="raise")
    if not (np.isfinite(df[PRICE]) & df[PRICE].ge(0)).all():
        raise ValueError("价格必须是非负且有限的数字，不能缺失")
    df["名称"] = df["名称"].astype("string").fillna("未命名商品")
    df["价格说明"] = df["价格说明"].astype("string").fillna("未标注")
    # 只展示 HTTP(S) 链接；不主动访问商品页面。
    df["商品链接"] = df["商品链接"].fillna("").map(
        lambda link: link if urlsplit(str(link)).scheme in {"http", "https"} else ""
    )
    df["同名待核查"] = df.duplicated(subset=["名称"], keep=False)
    df["价格区间"] = pd.cut(df[PRICE], bins=[0, 3000, 5000, 8000, np.inf], labels=LABELS, right=False)
    return df


def filter_data(df, keyword, price_range, notes, duplicates_only):
    mask = (
        df["名称"].str.contains(keyword.strip(), case=False, regex=False, na=False)
        & df[PRICE].between(*price_range)
        & df["价格说明"].isin(notes)
    )
    if duplicates_only:
        mask &= df["同名待核查"]
    return df.loc[mask].copy()
