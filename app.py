import streamlit as st
import pandas as pd
import pydeck as pdk

# 设置页面配置
st.set_page_config(page_title="5G 信号可视化看板", layout="wide")

st.title("📡 5G 信号可视化看板")
st.markdown("欢迎来到 **'Code with AI' 极客探索赛**！")

# ==========================================
# 1. 数据加载
# ==========================================
df = pd.read_csv("data/signal_samples.csv")

with st.container():
    st.subheader("数据预览")
    st.dataframe(df.head(10), use_container_width=True)

# ==========================================
# 2. 信号热力/散点地图（pydeck）
# ==========================================
st.subheader("信号强度地理分布")

# 为每个点根据 RSRP_dBm 分配颜色
def get_color(rsrp):
    if rsrp > -90:
        return [0, 255, 0, 160]       # 绿色：信号强
    elif rsrp < -110:
        return [255, 0, 0, 160]       # 红色：信号弱
    else:
        return [255, 255, 0, 160]     # 黄色：信号中等

df["color"] = df["RSRP_dBm"].apply(get_color)

# 计算地图中心
center_lat = df["Latitude"].mean()
center_lon = df["Longitude"].mean()

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["Longitude", "Latitude"],
    get_fill_color="color",
    get_radius=100,
    pickable=True,
    radius_min_pixels=5,
    radius_max_pixels=15,
)

view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=12,
    pitch=0,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "html": "<b>CellID:</b> {CellID}<br/><b>Band:</b> {Band}<br/><b>RSRP:</b> {RSRP_dBm} dBm<br/><b>终端类型:</b> {TerminalType}",
        "style": {"backgroundColor": "rgba(0,0,0,0.8)", "color": "white"},
    },
)

st.pydeck_chart(deck)

# 颜色图例说明
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<p style="text-align:center;color:green;font-weight:bold;font-size:18px;">🟢 RSRP > -90 dBm<br/><span style="font-size:14px;font-weight:normal;">信号强</span></p>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<p style="text-align:center;color:#CCCC00;font-weight:bold;font-size:18px;">🟡 -110 ~ -90 dBm<br/><span style="font-size:14px;font-weight:normal;">信号中等</span></p>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<p style="text-align:center;color:red;font-weight:bold;font-size:18px;">🔴 RSRP &lt; -110 dBm<br/><span style="font-size:14px;font-weight:normal;">信号弱</span></p>',
        unsafe_allow_html=True,
    )

# ==========================================
# 3. 数据概览图表
# ==========================================
st.subheader("数据概览")

chart_col1, chart_col2 = st.columns(2, gap="large")

# 柱状图：各频段（Band）的基站数量
with chart_col1:
    st.markdown("**各频段（Band）基站数量**")
    band_counts = df["Band"].value_counts().reset_index()
    band_counts.columns = ["Band", "Count"]

    st.bar_chart(band_counts.set_index("Band"), height=400)

# 饼状图：不同类型终端（TerminalType）的占比
with chart_col2:
    st.markdown("**不同类型终端（TerminalType）占比**")
    terminal_counts = df["TerminalType"].value_counts()

    # 用 Altair 绘制饼图（Streamlit 无原生饼图，借助 st.altair_chart）
    import altair as alt

    pie_data = terminal_counts.reset_index()
    pie_data.columns = ["TerminalType", "Count"]

    chart = (
        alt.Chart(pie_data)
        .mark_arc(innerRadius=0)
        .encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(
                field="TerminalType",
                type="nominal",
                scale=alt.Scale(
                    domain=["Smartphone", "CPE", "IoT"],
                    range=["#1f77b4", "#ff7f0e", "#2ca02c"],
                ),
            ),
            tooltip=["TerminalType", "Count"],
        )
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)

# 底部统计摘要
st.caption(
    f"共 {len(df)} 个采样点 · "
    f"频段: {', '.join(sorted(df['Band'].unique()))} · "
    f"终端类型: {', '.join(sorted(df['TerminalType'].unique()))}"
)
