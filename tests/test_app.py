"""
5G 信号可视化看板 — 单元测试

测试覆盖:
    - load_data : 数据加载完整性
    - get_color : 三种颜色分支及边界条件
    - filter_data : 频段筛选、RSRP 范围筛选、组合筛选
    - 数据结构 : 必需列和数据类型校验
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# 将项目根目录加入 sys.path，以便导入 app.py 中的函数
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import app


# =============================================
# Fixtures
# =============================================

@pytest.fixture(scope="module")
def raw_data() -> pd.DataFrame:
    """加载原始数据集，供测试用例复用。"""
    return app.load_data()


# =============================================
# 数据加载测试
# =============================================

class TestLoadData:
    """验证数据加载功能的正确性。"""

    def test_load_returns_dataframe(self, raw_data):
        """加载结果应为 DataFrame。"""
        assert isinstance(raw_data, pd.DataFrame)

    def test_load_not_empty(self, raw_data):
        """数据集不应为空。"""
        assert len(raw_data) > 0

    def test_required_columns_exist(self, raw_data):
        """必须包含所有必需的列。"""
        required = [
            "Latitude", "Longitude", "CellID", "Band",
            "RSRP_dBm", "SINR_dB", "TerminalType", "Download_Mbps",
        ]
        for col in required:
            assert col in raw_data.columns, f"缺少必需列: {col}"

    def test_no_null_in_required_columns(self, raw_data):
        """必需列中不应有空值。"""
        required = [
            "Latitude", "Longitude", "CellID", "Band",
            "RSRP_dBm", "TerminalType", "Download_Mbps",
        ]
        assert raw_data[required].isnull().sum().sum() == 0


# =============================================
# get_color 测试
# =============================================

class TestGetColor:
    """验证信号强度颜色映射逻辑。"""

    # (输入, 期待值, 场景说明)
    @pytest.mark.parametrize("rsrp, expected, desc", [
        (-70,  [0, 255, 0, 160],   "强信号：远大于 -90"),
        (-89,  [0, 255, 0, 160],   "强信号：临界 -90 之上 1 dB"),
        (-90,  [255, 255, 0, 160], "中信号：恰好等于 -90"),
        (-100, [255, 255, 0, 160], "中信号：区间内"),
        (-110, [255, 255, 0, 160], "中信号：恰好等于 -110"),
        (-111, [255, 0, 0, 160],   "弱信号：临界 -110 之下 1 dB"),
        (-120, [255, 0, 0, 160],   "弱信号：远小于 -110"),
    ])
    def test_color_boundaries(self, rsrp, expected, desc):
        """验证各阈值边界处的颜色返回值。"""
        assert app.get_color(rsrp) == expected, f"[{desc}] RSRP={rsrp} 期望 {expected}"


# =============================================
# filter_data 测试
# =============================================

class TestFilterData:
    """验证数据筛选逻辑的正确性。"""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """构造小型测试数据集。"""
        return pd.DataFrame({
            "Band":         ["n28", "n41", "n78", "n28"],
            "RSRP_dBm":     [-80, -100, -120, -95],
            "Download_Mbps": [100, 200, 300, 400],
            "SINR_dB":      [5, 10, 15, 20],
            "TerminalType": ["A", "B", "C", "A"],
        })

    # 用于筛选中不对下载速率/信噪比设限的默认全量范围
    _full_range = (0, 1000)
    _full_sinr = (-30, 30)

    def test_filter_by_single_band(self, sample_df):
        """筛选单个频段应只返回该频段数据。"""
        result = app.filter_data(sample_df, bands=["n28"],
                                 rsrp_range=(-130, -60),
                                 download_range=self._full_range,
                                 sinr_range=self._full_sinr)
        assert len(result) == 2
        assert (result["Band"] == "n28").all()

    def test_filter_by_multiple_bands(self, sample_df):
        """筛选多个频段应返回所有匹配频段的数据。"""
        result = app.filter_data(sample_df, bands=["n28", "n78"],
                                 rsrp_range=(-130, -60),
                                 download_range=self._full_range,
                                 sinr_range=self._full_sinr)
        assert len(result) == 3

    def test_filter_by_rsrp_range(self, sample_df):
        """RSRP 范围筛选应只返回区间内的数据（包含边界）。"""
        result = app.filter_data(sample_df, bands=["n28", "n41", "n78"],
                                 rsrp_range=(-110, -90),
                                 download_range=self._full_range,
                                 sinr_range=self._full_sinr)
        assert len(result) == 2
        assert (result["RSRP_dBm"] >= -110).all()
        assert (result["RSRP_dBm"] <= -90).all()

    def test_combined_filter(self, sample_df):
        """频段 + RSRP 组合筛选应取交集。"""
        result = app.filter_data(sample_df, bands=["n28"],
                                 rsrp_range=(-90, -80),
                                 download_range=self._full_range,
                                 sinr_range=self._full_sinr)
        assert len(result) == 1
        assert result.iloc[0]["Band"] == "n28"

    def test_no_match_returns_empty(self, sample_df):
        """无匹配条件时应返回空 DataFrame。"""
        result = app.filter_data(sample_df, bands=["invalid"],
                                 rsrp_range=(-130, -60),
                                 download_range=self._full_range,
                                 sinr_range=self._full_sinr)
        assert result.empty

    def test_filter_returns_copy(self, sample_df):
        """筛选应返回副本，不影响原始数据。"""
        original_len = len(sample_df)
        _ = app.filter_data(sample_df, bands=["n28"],
                            rsrp_range=(-130, -60),
                            download_range=self._full_range,
                            sinr_range=self._full_sinr)
        assert len(sample_df) == original_len

    def test_filter_by_download_range(self, sample_df):
        """下载速率范围筛选。"""
        result = app.filter_data(sample_df, bands=["n28", "n41", "n78"],
                                 rsrp_range=(-130, -60),
                                 download_range=(150, 350),
                                 sinr_range=self._full_sinr)
        assert len(result) == 2
        assert (result["Download_Mbps"] >= 150).all()
        assert (result["Download_Mbps"] <= 350).all()

    def test_filter_by_sinr_range(self, sample_df):
        """信噪比范围筛选。"""
        result = app.filter_data(sample_df, bands=["n28", "n41", "n78"],
                                 rsrp_range=(-130, -60),
                                 download_range=self._full_range,
                                 sinr_range=(8, 18))
        assert len(result) == 2
        assert (result["SINR_dB"] >= 8).all()
        assert (result["SINR_dB"] <= 18).all()

    def test_filter_by_all_ranges(self, sample_df):
        """四个维度同时筛选。"""
        result = app.filter_data(sample_df, bands=["n28", "n41"],
                                 rsrp_range=(-130, -60),
                                 download_range=(0, 500),
                                 sinr_range=(0, 30))
        assert len(result) == 3
