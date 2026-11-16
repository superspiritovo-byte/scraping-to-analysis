"""运行：.\.venv\Scripts\python.exe .\analyze_laptops.py"""

from pathlib import Path

import matplotlib

# 直接保存图片，批量运行时不用逐个关闭图表窗口。
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd


BASE = Path(__file__).resolve().parent
PRICE = "页面展示价格（元）"
LABELS = ["低于3000", "3000至不足5000", "5000至不足8000", "8000及以上"]


def save_chart(fig, output, filename):
    fig.tight_layout()
    fig.savefig(output / filename, dpi=150)
    plt.close(fig)


def main():
    source = BASE / "taobao_laptops_50.csv"
    output = BASE / "analysis_output"
    try:
        df = pd.read_csv(source, encoding="utf-8-sig")
    except UnicodeDecodeError:
        # 兼容中文 Windows/Excel 另存的 CSV。
        df = pd.read_csv(source, encoding="gb18030")
    required = {"名称", PRICE, "价格说明", "商品链接"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV 缺少列：{required - set(df.columns)}")
    if df.empty:
        raise ValueError("CSV 没有商品数据")

    clean = df.copy()
    clean[PRICE] = pd.to_numeric(clean[PRICE], errors="raise")
    if clean[PRICE].isna().any() or not clean[PRICE].between(0, float("inf"), inclusive="left").all():
        raise ValueError("价格必须是非负、有限且非空的数字，请先检查原始数据")

    clean["价格说明"] = clean["价格说明"].fillna("未标注")
    # 同名不等于同商品：仅标记，保留所有记录。
    clean["同名待核查"] = clean.duplicated(subset=["名称"], keep=False)
    clean["价格区间"] = pd.cut(
        clean[PRICE], bins=[0, 3000, 5000, 8000, float("inf")],
        labels=LABELS, right=False,
    )
    summary = clean.groupby("价格区间", observed=False).agg(
        商品数量=(PRICE, "count"), 平均价格=(PRICE, "mean"),
        最低价格=(PRICE, "min"), 最高价格=(PRICE, "max"),
    )
    summary["占比（%）"] = summary["商品数量"] / len(clean) * 100

    output.mkdir(exist_ok=True)
    clean.to_csv(output / "laptops_clean.csv", index=False, encoding="utf-8-sig")
    summary.round(2).to_csv(output / "price_summary.csv", encoding="utf-8-sig")
    clean[PRICE].describe().to_csv(output / "price_statistics.csv", encoding="utf-8-sig")

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(LABELS, summary["商品数量"], color="#348ABD")
    ax.bar_label(bars, padding=3)
    ax.set(title=f"{len(clean)}条商品的展示价格区间分布", xlabel="价格区间（元）", ylabel="商品数量")
    ax.set_ylim(0, summary["商品数量"].max() * 1.2)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    save_chart(fig, output, "price_bar.png")

    price = clean[PRICE]
    # 根据实际最高价格生成每1000元一个区间的边界。
    upper = (int(price.max()) // 1000 + 1) * 1000
    bins = range(0, upper + 1, 1000)
    for with_stats in (False, True):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(price, bins=bins, color="#348ABD", edgecolor="white")
        ax.set(title=f"{len(clean)}条商品的展示价格分布", xlabel="页面展示价格（元）", ylabel="商品数量")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        if with_stats:
            ax.axvline(price.mean(), color="red", linestyle="--", label=f"平均数：{price.mean():.2f}元")
            ax.axvline(price.median(), color="orange", linestyle="--", label=f"中位数：{price.median():.2f}元")
            ax.legend()
        save_chart(fig, output, "price_hist_stats.png" if with_stats else "price_hist.png")

    print(f"分析完成：{len(clean)}条商品")
    print(f"平均价格：{price.mean():.2f}元；中位数：{price.median():.2f}元")
    print(f"同名待核查：{int(clean['同名待核查'].sum())}条（未删除）")
    print(f"输出目录：{output}")
    print("说明：统计描述当前样本的页面展示价格，不代表销量或整个市场。")


if __name__ == "__main__":
    main()
