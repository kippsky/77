from __future__ import annotations

import os
from typing import List, Optional

import httpx
from pydantic import BaseModel

from app.models import ProductQuery, ProductOffer


class SerpApiResponseItem(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    source: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None


def parse_price_to_float(price_str: Optional[str]) -> Optional[float]:
    if not price_str:
        return None
    text = price_str.replace("￥", "").replace("¥", "").replace(",", "").strip()
    try:
        return float(text)
    except Exception:
        return None


class SerpAPIAdapter:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("SERPAPI_KEY")

    async def search_web(self, query: ProductQuery) -> List[SerpApiResponseItem]:
        if not self.api_key:
            return []
        params = {
            "engine": "google",
            "q": query.to_search_string(),
            "hl": "zh-CN",
            "gl": "cn",
            "num": 20,
            "tbm": "shop",
            "api_key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json()
        items: List[SerpApiResponseItem] = []
        # Prefer shopping results for richer data
        for sr in data.get("shopping_results", [])[:20]:
            items.append(
                SerpApiResponseItem(
                    title=sr.get("title"),
                    link=sr.get("link"),
                    source=sr.get("source"),
                    price=sr.get("price"),
                    rating=sr.get("rating"),
                    reviews=sr.get("reviews"),
                )
            )
        # Fallback to organic results if shopping empty
        if not items:
            for organic in data.get("organic_results", [])[:20]:
                items.append(
                    SerpApiResponseItem(
                        title=organic.get("title"),
                        link=organic.get("link"),
                        source=organic.get("source"),
                    )
                )
        return items

    @staticmethod
    def to_offer(item: SerpApiResponseItem) -> Optional[ProductOffer]:
        if not item.link:
            return None
        platform: Optional[str] = None
        if "taobao.com" in item.link or "tmall.com" in item.link:
            platform = "taobao"
        elif "jd.com" in item.link:
            platform = "jd"
        elif "xiaohongshu.com" in item.link:
            platform = "xhs"
        elif "douyin.com" in item.link:
            platform = "douyin"
        if not platform:
            return None
        return ProductOffer(
            platform=platform,
            product_title=item.title or "",
            shop_name=item.source or "",
            price=parse_price_to_float(item.price),
            product_url=item.link,
        )
