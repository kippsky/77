import streamlit as st
import pandas as pd
from utils import load_parquet

PURCHASE_PATH = "/workspace/data/purchase.parquet"
SALES_PATH = "/workspace/data/sales.parquet"

def render():
	st.header("查询模块")
	purchase = load_parquet(PURCHASE_PATH)
	sales = load_parquet(SALES_PATH)

	tab1, tab2 = st.tabs(["采购查询", "销售查询"])
	with tab1:
		if purchase is None:
			st.info("暂无采购数据")
		else:
			cols = st.columns(4)
			主体 = cols[0].selectbox("主体", options=["(全部)"] + sorted(purchase["主体"].dropna().unique().tolist()))
			公司 = cols[1].selectbox("公司", options=["(全部)"] + sorted(purchase["公司"].dropna().unique().tolist()))
			商品 = cols[2].selectbox("商品", options=["(全部)"] + sorted(purchase["商品"].dropna().unique().tolist()))
			日期范围 = cols[3].date_input("日期范围", [])
			df = purchase.copy()
			if 主体 != "(全部)":
				df = df[df["主体"] == 主体]
			if 公司 != "(全部)":
				df = df[df["公司"] == 公司]
			if 商品 != "(全部)":
				df = df[df["商品"] == 商品]
			if len(日期范围) == 2:
				df = df[(pd.to_datetime(df["日期"]) >= pd.to_datetime(日期范围[0])) & (pd.to_datetime(df["日期"]) <= pd.to_datetime(日期范围[1]))]
			st.dataframe(df, use_container_width=True)

	with tab2:
		if sales is None:
			st.info("暂无销售数据")
		else:
			cols = st.columns(4)
			主体 = cols[0].selectbox("主体", options=["(全部)"] + sorted(sales["主体"].dropna().unique().tolist()))
			公司 = cols[1].selectbox("公司", options=["(全部)"] + sorted(sales["公司"].dropna().unique().tolist()))
			商品 = cols[2].selectbox("商品", options=["(全部)"] + sorted(sales["商品"].dropna().unique().tolist()))
			日期范围 = cols[3].date_input("日期范围", [])
			df = sales.copy()
			if 主体 != "(全部)":
				df = df[df["主体"] == 主体]
			if 公司 != "(全部)":
				df = df[df["公司"] == 公司]
			if 商品 != "(全部)":
				df = df[df["商品"] == 商品]
			if len(日期范围) == 2:
				df = df[(pd.to_datetime(df["日期"]) >= pd.to_datetime(日期范围[0])) & (pd.to_datetime(df["日期"]) <= pd.to_datetime(日期范围[1]))]
			st.dataframe(df, use_container_width=True)