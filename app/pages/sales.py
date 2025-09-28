import streamlit as st
import pandas as pd
from utils import read_excel, mapping_ui, apply_mapping, convert_types, save_to_parquet, load_parquet, manual_entry_ui, export_excel

PARQUET_PATH = "/workspace/data/sales.parquet"

def render():
	st.header("销售模块")
	data = load_parquet(PARQUET_PATH)
	uploaded_df = pd.DataFrame()

	tab1, tab2 = st.tabs(["导入Excel", "手工录入"])
	with tab1:
		file = st.file_uploader("上传销售Excel", type=["xlsx", "xls"])
		if file is not None:
			raw = read_excel(file)
			st.write("源表头:", list(raw.columns))
			mapping = mapping_ui(list(raw.columns), "销售")
			if st.button("应用映射", key="map-sales"):
				mapped = apply_mapping(raw, mapping)
				mapped = convert_types(mapped, ["数量", "单价"])
				uploaded_df = mapped
				st.dataframe(mapped, use_container_width=True)

	with tab2:
		new_row = manual_entry_ui("销售")
		if not new_row.empty:
			if data is None:
				data = new_row
			else:
				data = pd.concat([data, new_row], ignore_index=True)
			save_to_parquet(data, PARQUET_PATH)
			st.success("已添加并保存")

	if uploaded_df is not None and not uploaded_df.empty:
		if st.button("保存导入数据", key="save-import-sales"):
			if data is None:
				data = uploaded_df
			else:
				data = pd.concat([data, uploaded_df], ignore_index=True)
			save_to_parquet(data, PARQUET_PATH)
			st.success("导入数据已保存")

	data = load_parquet(PARQUET_PATH)
	if data is not None:
		st.subheader("当前销售数据")
		st.dataframe(data, use_container_width=True)
		if st.button("导出销售数据"):
			export_excel(data, "销售数据.xlsx")