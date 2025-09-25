from __future__ import annotations

import threading
import webbrowser
from dataclasses import asdict
from tkinter import BOTH, END, LEFT, RIGHT, TOP, Button, DoubleVar, E, Entry, Frame, HORIZONTAL, Label, N, S, Scrollbar, StringVar, Tk, W
from tkinter import ttk
from typing import List, Optional

from app.aggregator import OfferAggregator
from app.adapters.douyin import DouyinAdapter
from app.adapters.jd import JDAdapter
from app.adapters.taobao import TaobaoAdapter
from app.adapters.xiaohongshu import XiaohongshuAdapter
from app.models import Offer, compute_score


class App:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("多平台商品价格/评论对比助手")
        self.root.geometry("1200x700")

        # Aggregator and adapters
        self.adapters = [TaobaoAdapter(), JDAdapter(), XiaohongshuAdapter(), DouyinAdapter()]
        self.aggregator = OfferAggregator(self.adapters)

        # Query variables
        self.var_product_name = StringVar()
        self.var_product_info = StringVar()

        # Weights for comparison
        self.var_weight_price = DoubleVar(value=0.6)
        self.var_weight_rating = DoubleVar(value=0.3)
        self.var_weight_reviews = DoubleVar(value=0.1)

        self._build_ui()

        # Data
        self.current_offers: List[Offer] = []

    def _build_ui(self) -> None:
        # Top input frame
        input_frame = Frame(self.root)
        input_frame.pack(side=TOP, fill="x", padx=10, pady=10)

        Label(input_frame, text="产品名称:").grid(row=0, column=0, sticky=E)
        Entry(input_frame, textvariable=self.var_product_name, width=40).grid(row=0, column=1, sticky=W, padx=6)

        Label(input_frame, text="补充信息:").grid(row=0, column=2, sticky=E)
        Entry(input_frame, textvariable=self.var_product_info, width=40).grid(row=0, column=3, sticky=W, padx=6)

        Button(input_frame, text="搜索", command=self._on_search).grid(row=0, column=4, padx=8)
        Button(input_frame, text="对比", command=self._on_compare).grid(row=0, column=5, padx=4)

        # Weights sliders
        weights_frame = Frame(self.root)
        weights_frame.pack(side=TOP, fill="x", padx=10)

        self._add_weight_slider(weights_frame, "价格权重", self.var_weight_price, 0)
        self._add_weight_slider(weights_frame, "评分权重", self.var_weight_rating, 1)
        self._add_weight_slider(weights_frame, "评论权重", self.var_weight_reviews, 2)

        # Main content split: left results, right details
        content_frame = Frame(self.root)
        content_frame.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)

        # Left: results and compare
        left_frame = Frame(content_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # Results Treeview
        Label(left_frame, text="搜索结果").pack(anchor=W)
        self.results_tree = self._create_tree(left_frame)
        self.results_tree.pack(fill=BOTH, expand=True)
        self.results_tree.bind("<<TreeviewSelect>>", self._on_select_result)

        # Compare Treeview
        Label(left_frame, text="对比结果").pack(anchor=W, pady=(10, 0))
        self.compare_tree = self._create_tree(left_frame)
        self.compare_tree.pack(fill=BOTH, expand=True)
        self.compare_tree.bind("<<TreeviewSelect>>", self._on_select_compare)

        # Right: details panel
        right_frame = Frame(content_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        Label(right_frame, text="详情").pack(anchor=W)
        self.details_text = ttk.Treeview(right_frame, columns=("field", "value"), show="headings")
        self.details_text.heading("field", text="字段")
        self.details_text.heading("value", text="值")
        self.details_text.column("field", width=120, anchor=W)
        self.details_text.column("value", width=300, anchor=W)
        self.details_text.pack(fill=BOTH, expand=True)

        Button(right_frame, text="打开链接", command=self._open_selected_url).pack(anchor=E, pady=6)

    def _add_weight_slider(self, parent: Frame, text: str, var: DoubleVar, col: int) -> None:
        frame = Frame(parent)
        frame.grid(row=0, column=col, padx=10, sticky=W)
        Label(frame, text=text).pack(anchor=W)
        scale = ttk.Scale(frame, from_=0.0, to=1.0, orient=HORIZONTAL, variable=var)
        scale.pack(fill="x")

    def _create_tree(self, parent: Frame) -> ttk.Treeview:
        columns = ("platform", "shop", "title", "price", "rating", "reviews", "url")
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        headings = {
            "platform": "平台",
            "shop": "店铺",
            "title": "标题",
            "price": "价格",
            "rating": "评分",
            "reviews": "评论数",
            "url": "链接",
        }
        widths = {"platform": 90, "shop": 150, "title": 380, "price": 80, "rating": 60, "reviews": 80, "url": 260}
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor=W)

        # Add y-scrollbar
        vsb = Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill="y")
        return tree

    def _on_search(self) -> None:
        query = self.var_product_name.get().strip()
        info = self.var_product_info.get().strip()
        if not query:
            return

        # Clear existing
        for t in (self.results_tree, self.compare_tree):
            for item in t.get_children():
                t.delete(item)
        self.details_text.delete(*self.details_text.get_children())

        def task() -> None:
            offers = self.aggregator.fetch_all(query, info)
            self.current_offers = offers
            self._populate_tree(self.results_tree, offers)

        threading.Thread(target=task, daemon=True).start()

    def _on_compare(self) -> None:
        if not self.current_offers:
            return

        offers = self.current_offers
        min_price = min((o.price for o in offers if o.price > 0), default=0.0)
        max_price = max((o.price for o in offers), default=1.0)

        weight_price = float(self.var_weight_price.get())
        weight_rating = float(self.var_weight_rating.get())
        weight_reviews = float(self.var_weight_reviews.get())

        scored = [
            (
                compute_score(
                    o,
                    min_price=min_price,
                    max_price=max_price,
                    weight_price=weight_price,
                    weight_rating=weight_rating,
                    weight_reviews=weight_reviews,
                ),
                o,
            )
            for o in offers
        ]
        scored.sort(key=lambda t: t[0], reverse=True)
        ranked = [o for _, o in scored]

        # Populate compare tree
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        self._populate_tree(self.compare_tree, ranked)

    def _populate_tree(self, tree: ttk.Treeview, offers: List[Offer]) -> None:
        for idx, o in enumerate(offers):
            tree.insert(
                "",
                END,
                iid=f"{id(tree)}-{idx}",
                values=(
                    o.platform,
                    o.shop_name,
                    o.product_title,
                    f"{o.price:.2f}",
                    f"{o.rating:.2f}",
                    o.review_count,
                    o.url,
                ),
            )

    def _offer_from_tree_selection(self, tree: ttk.Treeview) -> Optional[Offer]:
        sel = tree.selection()
        if not sel:
            return None
        values = tree.item(sel[0], "values")
        # Map back to offer by URL match (unique in our demo)
        url = values[6]
        for o in self.current_offers:
            if o.url == url:
                return o
        return None

    def _on_select_result(self, _event=None) -> None:  # noqa: ANN001
        offer = self._offer_from_tree_selection(self.results_tree)
        if offer:
            self._show_details(offer)

    def _on_select_compare(self, _event=None) -> None:  # noqa: ANN001
        offer = self._offer_from_tree_selection(self.compare_tree)
        if offer:
            self._show_details(offer)

    def _show_details(self, offer: Offer) -> None:
        self.details_text.delete(*self.details_text.get_children())
        data = asdict(offer)
        # Flatten extra
        extra = data.pop("extra", {}) or {}
        for k, v in data.items():
            self.details_text.insert("", END, values=(k, v))
        if extra:
            self.details_text.insert("", END, values=("—", "—"))
            for k, v in extra.items():
                self.details_text.insert("", END, values=(k, v))

    def _open_selected_url(self) -> None:
        offer = self._offer_from_tree_selection(self.results_tree) or self._offer_from_tree_selection(self.compare_tree)
        if offer and offer.url:
            webbrowser.open(offer.url)


def main() -> None:
    root = Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

