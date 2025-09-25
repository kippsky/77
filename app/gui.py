from __future__ import annotations

import asyncio
import os
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QDoubleSpinBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QTextEdit,
    QDialog,
    QFormLayout,
)

from app.models import ProductQuery, CompareCriteria, AggregatedResult, ComparedOffer
from app.aggregator import SearchAggregator


class WorkerThread(QThread):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, keyword: str, extra: str) -> None:
        super().__init__()
        self.keyword = keyword
        self.extra = extra

    def run(self) -> None:  # type: ignore[override]
        try:
            query = ProductQuery(keyword=self.keyword, extra_info=self.extra or None)
            aggregator = SearchAggregator()
            result: AggregatedResult = asyncio.run(aggregator.search_all(query))
            self.finished.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class DetailDialog(QDialog):
    def __init__(self, parent: QWidget, text: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("店铺与产品详情")
        layout = QVBoxLayout(self)
        te = QTextEdit(self)
        te.setReadOnly(True)
        te.setPlainText(text)
        layout.addWidget(te)


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("多平台比价工具 (淘宝/京东/小红书/抖音)")
        self.resize(1100, 700)
        self._result: Optional[AggregatedResult] = None
        self._compared: List[ComparedOffer] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)

        # 输入区
        row1 = QHBoxLayout()
        self.edt_keyword = QLineEdit(self)
        self.edt_keyword.setPlaceholderText("产品名称，如：iPhone 15 Pro Max")
        self.edt_extra = QLineEdit(self)
        self.edt_extra.setPlaceholderText("附加信息，如 256G 蓝色 国行")
        self.btn_search = QPushButton("搜索", self)
        self.btn_search.clicked.connect(self.on_search_clicked)
        row1.addWidget(QLabel("关键词：", self))
        row1.addWidget(self.edt_keyword, 2)
        row1.addWidget(QLabel("附加：", self))
        row1.addWidget(self.edt_extra, 2)
        row1.addWidget(self.btn_search)

        # 条件区
        row2 = QHBoxLayout()
        self.chk_price = QCheckBox("按价格")
        self.chk_price.setChecked(True)
        self.chk_reviews = QCheckBox("按评论数")
        self.spn_price_w = QDoubleSpinBox(self)
        self.spn_price_w.setRange(0, 10)
        self.spn_price_w.setValue(1.0)
        self.spn_reviews_w = QDoubleSpinBox(self)
        self.spn_reviews_w.setRange(0, 10)
        self.spn_reviews_w.setValue(1.0)
        self.btn_compare = QPushButton("比对", self)
        self.btn_compare.clicked.connect(self.on_compare_clicked)
        row2.addWidget(self.chk_price)
        row2.addWidget(QLabel("权重："))
        row2.addWidget(self.spn_price_w)
        row2.addSpacing(16)
        row2.addWidget(self.chk_reviews)
        row2.addWidget(QLabel("权重："))
        row2.addWidget(self.spn_reviews_w)
        row2.addStretch(1)
        row2.addWidget(self.btn_compare)

        # 结果区
        splitter = QSplitter(Qt.Orientation.Vertical, self)

        self.tbl_results = QTableWidget(self)
        self.tbl_results.setColumnCount(7)
        self.tbl_results.setHorizontalHeaderLabels([
            "平台", "标题", "店铺", "价格", "评论数", "评分", "链接",
        ])
        self.tbl_results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.tbl_compare = QTableWidget(self)
        self.tbl_compare.setColumnCount(8)
        self.tbl_compare.setHorizontalHeaderLabels([
            "分数", "平台", "标题", "店铺", "价格", "评论数", "评分", "链接",
        ])
        self.tbl_compare.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_compare.cellDoubleClicked.connect(self.on_compare_row_dbl_clicked)

        splitter.addWidget(self.tbl_results)
        splitter.addWidget(self.tbl_compare)

        root.addLayout(row1)
        root.addLayout(row2)
        root.addWidget(splitter, 1)

    def on_search_clicked(self) -> None:
        keyword = self.edt_keyword.text().strip()
        extra = self.edt_extra.text().strip()
        if not keyword:
            return
        self.btn_search.setEnabled(False)
        self.tbl_results.setRowCount(0)
        self.tbl_compare.setRowCount(0)
        self._result = None
        self._compared = []
        self.worker = WorkerThread(keyword, extra)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.failed.connect(self.on_search_failed)
        self.worker.start()

    def on_search_failed(self, msg: str) -> None:
        self.btn_search.setEnabled(True)
        self.tbl_results.setRowCount(0)
        self.tbl_results.setRowCount(1)
        self.tbl_results.setItem(0, 0, QTableWidgetItem("错误"))
        self.tbl_results.setItem(0, 1, QTableWidgetItem(msg))

    def on_search_finished(self, result: AggregatedResult) -> None:
        self.btn_search.setEnabled(True)
        self._result = result
        rows = len(result.offers)
        self.tbl_results.setRowCount(rows)
        for i, o in enumerate(result.offers):
            self.tbl_results.setItem(i, 0, QTableWidgetItem(o.platform))
            self.tbl_results.setItem(i, 1, QTableWidgetItem(o.product_title or ""))
            self.tbl_results.setItem(i, 2, QTableWidgetItem(o.shop_name or ""))
            self.tbl_results.setItem(i, 3, QTableWidgetItem(f"{o.price if o.price is not None else ''}"))
            self.tbl_results.setItem(i, 4, QTableWidgetItem(f"{o.reviews_count if o.reviews_count is not None else ''}"))
            self.tbl_results.setItem(i, 5, QTableWidgetItem(f"{o.rating if o.rating is not None else ''}"))
            self.tbl_results.setItem(i, 6, QTableWidgetItem(o.product_url or ""))

    def on_compare_clicked(self) -> None:
        if not self._result:
            return
        criteria = CompareCriteria(
            by_price=self.chk_price.isChecked(),
            by_reviews=self.chk_reviews.isChecked(),
            price_weight=float(self.spn_price_w.value()),
            reviews_weight=float(self.spn_reviews_w.value()),
        )
        compared = SearchAggregator.compare_offers(self._result, criteria)
        self._compared = compared
        rows = len(compared)
        self.tbl_compare.setRowCount(rows)
        for i, c in enumerate(compared):
            o = c.offer
            self.tbl_compare.setItem(i, 0, QTableWidgetItem(f"{c.score:.3f}"))
            self.tbl_compare.setItem(i, 1, QTableWidgetItem(o.platform))
            self.tbl_compare.setItem(i, 2, QTableWidgetItem(o.product_title or ""))
            self.tbl_compare.setItem(i, 3, QTableWidgetItem(o.shop_name or ""))
            self.tbl_compare.setItem(i, 4, QTableWidgetItem(f"{o.price if o.price is not None else ''}"))
            self.tbl_compare.setItem(i, 5, QTableWidgetItem(f"{o.reviews_count if o.reviews_count is not None else ''}"))
            self.tbl_compare.setItem(i, 6, QTableWidgetItem(f"{o.rating if o.rating is not None else ''}"))
            self.tbl_compare.setItem(i, 7, QTableWidgetItem(o.product_url or ""))

    def on_compare_row_dbl_clicked(self, row: int, column: int) -> None:  # noqa: ARG002
        if row < 0 or row >= len(self._compared):
            return
        c = self._compared[row]
        o = c.offer
        detail = (
            f"平台: {o.platform}\n"
            f"标题: {o.product_title}\n"
            f"店铺: {o.shop_name}\n"
            f"价格: {o.price}\n"
            f"评论数: {o.reviews_count}\n"
            f"评分: {o.rating}\n"
            f"销量: {o.sales_count}\n"
            f"商品链接: {o.product_url}\n"
            f"店铺链接: {o.shop_url}\n"
        )
        dlg = DetailDialog(self, detail)
        dlg.exec()


def run_app() -> None:
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.exec()

