import io
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st


REQUIRED_FIELDS = ["主体", "公司", "商品", "数量", "单价", "日期"]


@st.cache_data(show_spinner=False)
def read_excel(file) -> pd.DataFrame:
	return pd.read_excel(file)


@st.cache_data(show_spinner=False)
def convert_types(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
	for col in numeric_cols:
		if col in df.columns:
			df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
	if "日期" in df.columns:
		df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
	return df


@st.cache_data(show_spinner=False)
def save_to_parquet(df: pd.DataFrame, path: str):
	df.to_parquet(path, index=False)


@st.cache_data(show_spinner=False)
def load_parquet(path: str) -> Optional[pd.DataFrame]:
	try:
		return pd.read_parquet(path)
	except Exception:
		return None


def mapping_ui(src_columns: List[str], kind: str) -> Dict[str, str]:
	st.subheader(f"{kind}字段映射")
	mapping: Dict[str, str] = {}
	cols = st.columns(3)
	for i, field in enumerate(REQUIRED_FIELDS):
		with cols[i % 3]:
			default_index = src_columns.index(field) + 1 if field in src_columns else 0
			mapping[field] = st.selectbox(
				f"映射 {field}",
				options=["(不映射)"] + src_columns,
				index=default_index,
				key=f"{kind}-{field}",
			)
	return mapping


def apply_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
	out = pd.DataFrame()
	for target, source in mapping.items():
		if source and source != "(不映射)" and source in df.columns:
			out[target] = df[source]
	return out


def manual_entry_ui(kind: str) -> pd.DataFrame:
	st.subheader(f"{kind}手工录入")
	with st.expander("新增一行"):
		cols = st.columns(6)
		主体 = cols[0].text_input("主体")
		公司 = cols[1].text_input("公司")
		商品 = cols[2].text_input("商品")
		数量 = cols[3].number_input("数量", value=0.0, step=1.0)
		单价 = cols[4].number_input("单价", value=0.0, step=0.01, format="%.4f")
		日期 = cols[5].date_input("日期")
		if st.button("添加记录", key=f"add-{kind}"):
			return pd.DataFrame([
				{"主体": 主体, "公司": 公司, "商品": 商品, "数量": 数量, "单价": 单价, "日期": pd.to_datetime(日期)}
			])
	return pd.DataFrame(columns=REQUIRED_FIELDS)


def export_excel(df: pd.DataFrame, filename: str):
	if df.empty:
		st.warning("没有可导出的数据")
		return
	# 保存到磁盘
	path = f"/workspace/export/{filename}"
	df.to_excel(path, index=False)
	st.success(f"已导出: {path}")

	# 提供下载按钮
	buffer = io.BytesIO()
	with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
		df.to_excel(writer, index=False)
	buffer.seek(0)
	st.download_button(
		"下载Excel",
		data=buffer.getvalue(),
		file_name=filename,
		mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	) 