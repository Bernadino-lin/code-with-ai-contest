# 5G 信号可视化看板

基于 Streamlit 构建的 5G 信号数据交互式可视化看板，支持地理空间信号强度分析、多维数据筛选与图表统计。

## 功能概览

### 3D 信号地图
- 使用 pydeck `ColumnLayer` 将采样点渲染为 3D 柱状图
- 柱体颜色按 RSRP 信号强度分级：绿色（强）、黄色（中）、红色（弱）
- 柱体高度反映下载速率（Download_Mbps）
- 支持鼠标悬停查看详情的 tooltip

### 侧边栏联动筛选
- **频段 (Band)**：多选下拉框
- **RSRP 范围**：滑动条
- **下载速率**：滑动条
- **信噪比 SINR**：滑动条
- 所有筛选器实时联动更新地图与图表

### 数据概览图表
- **柱状图**：各频段基站数量统计
- **饼图**：各终端类型（Smartphone / CPE / IoT）占比（百分比嵌入图例）

### 单元测试
- 覆盖数据加载、颜色映射、多维筛选逻辑，共 20 项测试用例

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`。

### 3. 运行测试

```bash
python -m pytest tests/test_app.py -v
```

## 项目结构

```
├── app.py                 # Streamlit 应用主程序
├── requirements.txt       # Python 依赖
├── data/
│   └── signal_samples.csv # 5G 信号采样数据
├── tests/
│   └── test_app.py        # 单元测试
└── README.md
```

## 数据字段说明

| 字段 | 说明 |
|------|------|
| Latitude | 纬度 |
| Longitude | 经度 |
| CellID | 小区 ID |
| Band | 5G 频段（n28 / n41 / n78） |
| RSRP_dBm | 参考信号接收功率（dBm） |
| SINR_dB | 信噪比（dB） |
| TerminalType | 终端类型（Smartphone / CPE / IoT） |
| Download_Mbps | 下载速率（Mbps） |
