import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

# =============================================
# 常量定义
# =============================================
DATA_PATH = "data/signal_samples.csv"


# =============================================
# 核心业务函数
# =============================================

def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    """从 CSV 文件加载 5G 信号采样数据。

    Returns:
        包含 Latitude、Longitude、CellID、Band、RSRP_dBm、
        SINR_dB、TerminalType、Download_Mbps 等列的 DataFrame。
    """
    return pd.read_csv(path)


def get_color(rsrp: float) -> list:
    """根据 RSRP 值返回 RGBA 颜色数组，用于地图着色。

    信号强度颜色映射（3GPP 推荐阈值）:
        > -90 dBm  → 绿色   [0, 255, 0, 160]   信号强
        < -110 dBm → 红色   [255, 0, 0, 160]   信号弱
        其余        → 黄色   [255, 255, 0, 160]  信号中等

    Args:
        rsrp: RSRP 值，单位为 dBm。

    Returns:
        长度为 4 的 RGBA 颜色列表。
    """
    if rsrp > -90:
        return [0, 255, 0, 160]
    if rsrp < -110:
        return [255, 0, 0, 160]
    return [255, 255, 0, 160]


def filter_data(df: pd.DataFrame, bands: list, rsrp_range: tuple,
                download_range: tuple, sinr_range: tuple) -> pd.DataFrame:
    """根据频段、RSRP 范围、下载速率范围和信噪比范围筛选数据。

    Args:
        df: 原始数据框。
        bands: 需保留的频段列表。
        rsrp_range: (最小值, 最大值) 元组。
        download_range: 下载速率范围 (Mbps)。
        sinr_range: 信噪比范围 (dB)。

    Returns:
        筛选后的数据框副本。
    """
    mask = (
        df["Band"].isin(bands)
        & df["RSRP_dBm"].between(rsrp_range[0], rsrp_range[1])
        & df["Download_Mbps"].between(download_range[0], download_range[1])
        & df["SINR_dB"].between(sinr_range[0], sinr_range[1])
    )
    return df[mask].copy()


# =============================================
# Streamlit 应用入口
# =============================================

st.set_page_config(page_title="5G 信号可视化看板", layout="wide")

# ---------- 侧边栏筛选器 ----------
st.sidebar.title("📡 筛选条件")

df_raw = load_data()

available_bands = sorted(df_raw["Band"].unique())
selected_bands = st.sidebar.multiselect(
    "频段 (Band)",
    options=available_bands,
    default=available_bands,
)

rsrp_min = int(df_raw["RSRP_dBm"].min())
rsrp_max = int(df_raw["RSRP_dBm"].max())
rsrp_range = st.sidebar.slider(
    "RSRP 范围 (dBm)",
    min_value=rsrp_min,
    max_value=rsrp_max,
    value=(rsrp_min, rsrp_max),
    step=1,
)

download_min = int(df_raw["Download_Mbps"].min())
download_max = int(df_raw["Download_Mbps"].max())
download_range = st.sidebar.slider(
    "下载速率 (Mbps)",
    min_value=download_min,
    max_value=download_max,
    value=(download_min, download_max),
    step=1,
)

sinr_min = int(df_raw["SINR_dB"].min())
sinr_max = int(df_raw["SINR_dB"].max())
sinr_range = st.sidebar.slider(
    "信噪比 SINR (dB)",
    min_value=sinr_min,
    max_value=sinr_max,
    value=(sinr_min, sinr_max),
    step=1,
)

df = filter_data(df_raw, selected_bands, rsrp_range, download_range, sinr_range)

st.sidebar.divider()
st.sidebar.metric("📊 筛选后样本数", len(df))
st.sidebar.caption(f"总样本数: {len(df_raw)}")

# ---------- 主内容区 ----------
st.title("📡 5G 信号可视化看板")
st.markdown("欢迎来到 **'Code with AI' 极客探索赛**！")

# 筛选为空时的兜底处理
if df.empty:
    st.warning("⚠️ 当前筛选条件下无数据，请调整侧边栏的筛选条件。")
    st.stop()

# ---------- 3D 信号地图 ----------
st.subheader("🗺️ 信号强度地理分布 (3D)")

df["color"] = df["RSRP_dBm"].apply(get_color)

center_lat = df["Latitude"].mean()
center_lon = df["Longitude"].mean()

# 使用 ColumnLayer 实现 3D 柱状图，高度 = 下载速率 × 缩放系数
column_layer = pdk.Layer(
    "ColumnLayer",
    data=df,
    get_position=["Longitude", "Latitude"],
    get_elevation="Download_Mbps",
    elevation_scale=0.3,
    radius=50,
    get_fill_color="color",
    pickable=True,
    auto_highlight=True,
    extruded=True,          # 开启 3D 挤出效果
)

view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=12,
    pitch=45,               # 倾斜视角以突显 3D 效果
    bearing=0,
)

deck = pdk.Deck(
    layers=[column_layer],
    initial_view_state=view_state,
    tooltip={
        "html": (
            "<b>CellID:</b> {CellID}<br/>"
            "<b>Band:</b> {Band}<br/>"
            "<b>RSRP:</b> {RSRP_dBm} dBm<br/>"
            "<b>📥 下载速率:</b> {Download_Mbps} Mbps<br/>"
            "<b>终端类型:</b> {TerminalType}"
        ),
        "style": {"backgroundColor": "rgba(0,0,0,0.8)", "color": "white"},
    },
)

st.pydeck_chart(deck)

# 颜色图例
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<p style="text-align:center;color:green;font-weight:bold;font-size:18px;">'
        "🟢 RSRP > -90 dBm<br/>"
        '<span style="font-size:14px;font-weight:normal;">信号强</span></p>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<p style="text-align:center;color:#CCCC00;font-weight:bold;font-size:18px;">'
        "🟡 -110 ~ -90 dBm<br/>"
        '<span style="font-size:14px;font-weight:normal;">信号中等</span></p>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<p style="text-align:center;color:red;font-weight:bold;font-size:18px;">'
        "🔴 RSRP &lt; -110 dBm<br/>"
        '<span style="font-size:14px;font-weight:normal;">信号弱</span></p>',
        unsafe_allow_html=True,
    )

# ---------- 数据概览图表 ----------
st.subheader("📊 数据概览")

chart_col1, chart_col2 = st.columns(2, gap="large")

# 柱状图：各频段的基站数量
with chart_col1:
    st.markdown("**各频段（Band）基站数量**")
    band_counts = df["Band"].value_counts().reset_index()
    band_counts.columns = ["Band", "Count"]
    st.bar_chart(band_counts.set_index("Band"), height=400)

# 饼图：不同类型终端的占比（含百分比标签）
with chart_col2:
    st.markdown("**不同类型终端（TerminalType）占比**")
    terminal_counts = df["TerminalType"].value_counts()
    pie_data = terminal_counts.reset_index()
    pie_data.columns = ["TerminalType", "Count"]
    pie_data["Percentage"] = (
        pie_data["Count"] / pie_data["Count"].sum() * 100
    ).round(1)
    # 将百分比嵌入图例标签，避免扇区上叠加文字导致重叠
    pie_data["Legend"] = pie_data.apply(
        lambda r: f"{r['TerminalType']}  ({r['Percentage']}%)", axis=1
    )

    # 构造图例域（终端类型 + 百分比），确保与数据顺序一致
    legend_domain = list(pie_data["Legend"])
    color_range = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    pie_chart = (
        alt.Chart(pie_data)
        .mark_arc()
        .encode(
            theta=alt.Theta(field="Count", type="quantitative", sort=None),
            color=alt.Color(
                field="Legend",
                type="nominal",
                scale=alt.Scale(domain=legend_domain, range=color_range),
                legend=alt.Legend(title="终端类型"),
            ),
            tooltip=[
                alt.Tooltip("TerminalType:N", title="终端类型"),
                alt.Tooltip("Count:Q", title="数量"),
                alt.Tooltip("Percentage:Q", title="占比 (%)", format=".1f"),
            ],
        )
        .properties(height=400)
    )

    st.altair_chart(pie_chart, use_container_width=True)

# ---------- 底部统计摘要 ----------
st.caption(
    f"共 {len(df)} 个采样点（已筛选） · "
    f"频段: {', '.join(sorted(df['Band'].unique()))} · "
    f"终端类型: {', '.join(sorted(df['TerminalType'].unique()))}"
)
