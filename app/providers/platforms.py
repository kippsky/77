from __future__ import annotations

from typing import List

from app.models import ProductQuery, ProductOffer
from app.providers.base import SearchProvider
from app.providers.serpapi_adapter import SerpAPIAdapter


class SerpProvider(SearchProvider):
    platform = "serp"

    def __init__(self) -> None:
        self.adapter = SerpAPIAdapter()

    async def search(self, query: ProductQuery) -> List[ProductOffer]:
        items = await self.adapter.search_web(query)
        offers: List[ProductOffer] = []
        for item in items:
            offer = self.adapter.to_offer(item)
            if offer:
                offers.append(offer)
        return offers


class MockProvider(SearchProvider):
    platform = "mock"

    async def search(self, query: ProductQuery) -> List[ProductOffer]:
        text = query.to_search_string()
        return [
            ProductOffer(
                platform="taobao",
                product_title=f"{text} 官方旗舰店",
                shop_name="阿里自营旗舰店",
                price=4999.0,
                reviews_count=123456,
                rating=4.8,
                product_url="https://item.taobao.com/item.htm?mock=1",
                shop_url="https://shop.taobao.com/mock",
            ),
            ProductOffer(
                platform="jd",
                product_title=f"{text} 京东自营",
                shop_name="京东自营",
                price=5099.0,
                reviews_count=256000,
                rating=4.9,
                product_url="https://item.jd.com/1000000000.html",
                shop_url="https://mall.jd.com/mock",
            ),
            ProductOffer(
                platform="xhs",
                product_title=f"{text} 小红书好物",
                shop_name="小红书精选",
                price=4988.0,
                reviews_count=5600,
                rating=4.7,
                product_url="https://www.xiaohongshu.com/board/mock",
                shop_url="https://www.xiaohongshu.com/user/mock",
            ),
            ProductOffer(
                platform="douyin",
                product_title=f"{text} 抖音商城",
                shop_name="抖音优选",
                price=4950.0,
                reviews_count=9800,
                rating=4.6,
                product_url="https://mall.douyin.com/product/mock",
                shop_url="https://www.douyin.com/user/mock",
            ),
        ]
