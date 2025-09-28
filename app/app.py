import streamlit as st
from pages import purchase, sales, inventory, query

st.set_page_config(page_title="大宗交易进销存", layout="wide")

st.title("大宗交易进销存系统")

PAGES = {
    "采购模块": purchase.render,
    "销售模块": sales.render,
    "库存模块": inventory.render,
    "查询模块": query.render,
}

choice = st.sidebar.radio("模块", list(PAGES.keys()))
PAGES[choice]()
