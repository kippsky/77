import streamlit as st
import pandas as pd
from utils import load_parquet, export_excel

PURCHASE_PATH = "/workspace/data/purchase.parquet"
SALES_PATH = "/workspace/data/sales.parquet"

def compute_inventory(purchase: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
	if purchase is None:
		purchase = pd.DataFrame(columns=["主体", "公司", "商品", "数量", "单价", "日期"])
	if sales is None:
		sales = pd.DataFrame(columns=["主体", "公司", "商品", "数量", "单价", "日期"])
	purchase["数量"] = pd.to_numeric(purchase.get("数量", 0), errors="coerce").fillna(0)
	sales["数量"] = pd.to_numeric(sales.get("数量", 0), errors="coerce").fillna(0)

	# 汇总采购和销售
	purchase_amount = (pd.to_numeric(purchase.get("数量", 0), errors="coerce").fillna(0) * pd.to_numeric(purchase.get("单价", 0), errors="coerce").fillna(0))
	sales_amount = (pd.to_numeric(sales.get("数量", 0), errors="coerce").fillna(0) * pd.to_numeric(sales.get("单价", 0), errors="coerce").fillna(0))
	purchase_group = purchase.assign(_金额=purchase_amount).groupby(["主体", "公司", "商品"], dropna=False).agg(采购数量=("数量", "sum"), 采购金额=("_金额", "sum"))
	sales_group = sales.assign(_金额=sales_amount).groupby(["主体", "公司", "商品"], dropna=False).agg(销售数量=("数量", "sum"), 销售金额=("_金额", "sum"))

	inv = purchase_group.join(sales_group, how="outer").fillna(0)
	inv["结存数量"] = inv["采购数量"] - inv["销售数量"]
	inv["采购均价"] = inv.apply(lambda r: (r["采购金额"] / r["采购数量"]) if r["采购数量"] else 0, axis=1)
	inv = inv.reset_index()
	return inv

def render():
	st.header("库存模块")
	purchase = load_parquet(PURCHASE_PATH)
	sales = load_parquet(SALES_PATH)

	if purchase is not None:
		st.caption("采购记录数: " + str(len(purchase)))
	if sales is not None:
		st.caption("销售记录数: " + str(len(sales)))

	if st.button("生成库存结果"):
		inv = compute_inventory(purchase, sales)
		st.dataframe(inv, use_container_width=True)
		if st.button("导出库存结果"):
			export_excel(inv, "库存结果.xlsx")