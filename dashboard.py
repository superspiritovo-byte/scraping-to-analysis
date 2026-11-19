"""本机启动：python -m streamlit run dashboard.py"""

from pathlib import Path

import altair as alt
import streamlit as st

from dashboard_data import LABELS, PRICE, filter_data, load_data, load_mysql_data

BASE = Path(__file__).resolve().parent
st.set_page_config(page_title="笔记本商品观察台", page_icon="📊", layout="wide")
st.markdown("""
<style>
.stApp {background:#f3f6fa; color:#152e4d;}
.block-container {padding-top:2rem; max-width:1500px;}
h1 {font-weight:750!important; letter-spacing:-.04em;}
[data-testid="stMetric"] {background:white; padding:14px 10px; border-top:3px solid #2475bc; border-radius:4px;}
[data-testid="stMetricLabel"] {color:#48617d;}
[data-testid="stMetricValue"] {font-variant-numeric:tabular-nums; font-size:1.35rem;}
[data-testid="stSidebar"] {background:#e8eef5;}
[data-testid="stSidebar"] h2 {font-size:1.15rem;}
</style>
""", unsafe_allow_html=True)

st.title("笔记本商品观察台")
st.caption("从采集到分析 · 探索商品展示价格，核对数据细节")
secrets_path = BASE / ".streamlit" / "secrets.toml"
mysql_config = None
if secrets_path.exists():
    import tomllib
    try:
        with secrets_path.open("rb") as file:
            mysql_config = tomllib.load(file).get("mysql")
    except (OSError, ValueError):
        st.error("本机 secrets.toml 配置无法读取，请检查 TOML 格式。")
        st.stop()
source_label = "MySQL 清洗视图" if mysql_config is not None else "CSV 文件"
st.caption(f"数据来源：{source_label} · 页面每次重新运行都会读取最新数据")
st.button("刷新数据", key="refresh_data")
try:
    df = load_mysql_data(mysql_config) if mysql_config is not None else load_data(BASE / "taobao_laptops_50.csv")
except (OSError, ValueError) as exc:
    st.error(f"无法读取商品数据：{exc}")
    st.info("请检查 MySQL 本机配置和清洗视图；未配置 MySQL 时检查 taobao_laptops_50.csv。修正后点击刷新数据。")
    st.stop()

minimum, maximum = float(df[PRICE].min()), float(df[PRICE].max())
note_options = sorted(df["价格说明"].unique().tolist())


def reset_filters():
    for key in ("keyword", "budget", "notes", "duplicates", "order"):
        st.session_state.pop(key, None)


with st.sidebar:
    st.header("筛选商品")
    st.caption(f"本地样本 · 共 {len(df)} 条")
    keyword = st.text_input("商品名称关键词", key="keyword", placeholder="例如：联想、RTX、轻薄")
    if minimum < maximum:
        budget = st.slider("展示价格范围（元）", minimum, maximum, (minimum, maximum), step=1.0, key="budget")
    else:
        budget = (minimum, maximum)
        st.caption(f"所有商品均为 ¥{minimum:,.2f}")
    notes = st.multiselect("价格说明", note_options, default=note_options, key="notes")
    duplicates = st.checkbox("仅看同名待核查商品", key="duplicates")
    st.button("重置筛选", key="reset_filters", on_click=reset_filters, width="stretch")
    st.divider()
    st.caption("筛选范围包含两端价格。清空价格说明将不显示商品。")
    st.caption("同名仅作标记，不自动删除。链接保留采集时的原地址，可能经过广告跳转。")

selected = filter_data(df, keyword, budget, notes, duplicates)
st.caption(f"当前显示 {len(selected)} / {len(df)} 条 · 以下指标、图表和明细均随筛选更新")
metrics = st.columns(5)
metrics[0].metric("商品数量", f"{len(selected)}", help=f"占全部样本 {len(selected) / len(df):.0%}")
for column, title, method in zip(metrics[1:], ["平均展示价", "价格中位数", "最低展示价", "最高展示价"], ["mean", "median", "min", "max"]):
    value = getattr(selected[PRICE], method)() if len(selected) else None
    column.metric(title, f"¥{value:,.2f}" if value is not None else "—")

st.write("")
if selected.empty:
    st.info("没有符合条件的商品。请扩大价格范围、调整关键词，或点击左侧「重置筛选」。")
    st.stop()

left, right = st.columns([1, 1.25], gap="large")
with left:
    st.subheader("价格区间")
    st.caption("按固定区间比较商品数量")
    counts = selected["价格区间"].value_counts(sort=False).rename_axis("价格区间").reset_index(name="商品数量")
    counts["价格区间"] = counts["价格区间"].astype(str)
    bars = alt.Chart(counts).mark_bar(color="#2475bc", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("价格区间:N", sort=LABELS, axis=alt.Axis(labelAngle=0, labelLimit=160), title=None),
        y=alt.Y("商品数量:Q", axis=alt.Axis(tickMinStep=1), title="条"),
        tooltip=["价格区间:N", "商品数量:Q"],
    )
    labels = bars.mark_text(dy=-9, color="#152e4d").encode(text="商品数量:Q")
    st.altair_chart((bars + labels).properties(height=280), width="stretch")
with right:
    st.subheader("展示价格分布")
    st.caption("每 1000 元一组 · 蓝线为均价，橙线为中位数")
    histogram = alt.Chart(selected).mark_bar(color="#76a9d2", stroke="white").encode(
        x=alt.X(f"{PRICE}:Q", bin=alt.Bin(step=1000), title="展示价格（元）"),
        y=alt.Y("count():Q", title="条", axis=alt.Axis(tickMinStep=1)),
        tooltip=[alt.Tooltip(f"{PRICE}:Q", bin=alt.Bin(step=1000), title="价格区间"), alt.Tooltip("count():Q", title="商品数量")],
    )
    import pandas as pd
    references = pd.DataFrame({"数值": [selected[PRICE].mean(), selected[PRICE].median()], "指标": ["均价", "中位数"]})
    lines = alt.Chart(references).mark_rule(strokeDash=[5, 4], size=2).encode(
        x="数值:Q", color=alt.Color("指标:N", scale=alt.Scale(domain=["均价", "中位数"], range=["#16558d", "#d37b27"]), legend=None),
        tooltip=["指标:N", alt.Tooltip("数值:Q", format=".2f")],
    )
    st.altair_chart((histogram + lines).properties(height=280), width="stretch")

st.divider()
table_heading, order_column = st.columns([3, 1])
table_heading.subheader("商品明细")
order = order_column.selectbox("排序方式", ["页面原始顺序", "价格从低到高", "价格从高到低"], key="order", label_visibility="collapsed")
if order != "页面原始顺序":
    selected = selected.sort_values(PRICE, ascending=order == "价格从低到高", kind="stable")
view = selected[["名称", PRICE, "价格说明", "同名待核查", "商品链接"]]
st.dataframe(view, hide_index=True, width="stretch", height=420, column_config={
    "名称": st.column_config.TextColumn("商品名称", width="large"),
    PRICE: st.column_config.NumberColumn("展示价格（元）", format="¥%.2f"),
    "商品链接": st.column_config.LinkColumn("商品链接", display_text="查看商品"),
})
st.download_button("导出当前筛选结果 CSV", data=view.to_csv(index=False).encode("utf-8-sig"), file_name="laptops_filtered.csv", mime="text/csv")
st.caption(f"当前结果：未标注价格说明 {int(selected['价格说明'].eq('未标注').sum())} 条，同名待核查 {int(selected['同名待核查'].sum())} 条。")
st.caption("数据口径：本地保存的搜索结果样本，非实时行情；不同商品可能包含不同配置、优惠和补贴条件。数量不代表销量，统计不代表整个市场。")
