from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field


class ProductQuery(BaseModel):
    keyword: str = Field(..., description="产品关键词，如 iPhone 15 Pro Max")
    extra_info: Optional[str] = Field(
        None, description="附加信息，如颜色/容量/型号等，用于提高匹配度"
    )

    def to_search_string(self) -> str:
        if self.extra_info:
            return f"{self.keyword} {self.extra_info}"
        return self.keyword


class ProductOffer(BaseModel):
    platform: str = Field(..., description="平台：taobao/jd/xhs/douyin")
    product_title: str = Field(..., description="商品标题")
    shop_name: str = Field(..., description="店铺名称")
    price: Optional[float] = Field(None, description="价格，单位元")
    currency: str = Field("CNY", description="币种")
    reviews_count: Optional[int] = Field(None, description="评论/评价数量")
    rating: Optional[float] = Field(None, description="评分，0-5 或 0-100 区间")
    sales_count: Optional[int] = Field(None, description="销量，若可获取")
    product_url: Optional[str] = Field(None, description="商品链接")
    shop_url: Optional[str] = Field(None, description="店铺主页链接")


class AggregatedResult(BaseModel):
    query: ProductQuery
    offers: List[ProductOffer]


class CompareCriteria(BaseModel):
    by_price: bool = True
    by_reviews: bool = False
    price_weight: float = 1.0
    reviews_weight: float = 1.0


class ComparedOffer(BaseModel):
    offer: ProductOffer
    score: float
