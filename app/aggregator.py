from __future__ import annotations

import asyncio
from typing import List

from rapidfuzz import fuzz

from app.models import (
    ProductQuery,
    ProductOffer,
    AggregatedResult,
    CompareCriteria,
    ComparedOffer,
)
from app.providers.platforms import SerpProvider, MockProvider


def normalize_score(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.0
    return (value - min_value) / (max_value - min_value)


class SearchAggregator:
    def __init__(self) -> None:
        self.providers = [SerpProvider(), MockProvider()]

    async def search_all(self, query: ProductQuery) -> AggregatedResult:
        results: List[List[ProductOffer]] = await asyncio.gather(
            *[provider.search(query) for provider in self.providers], return_exceptions=False
        )
        offers: List[ProductOffer] = []
        for group in results:
            offers.extend(group)

        # 去重：基于标题模糊相似度
        deduped: List[ProductOffer] = []
        for offer in offers:
            if not offer.product_title:
                deduped.append(offer)
                continue
            is_dup = False
            for kept in deduped:
                if fuzz.token_set_ratio(offer.product_title, kept.product_title) >= 92:
                    is_dup = True
                    break
            if not is_dup:
                deduped.append(offer)

        return AggregatedResult(query=query, offers=deduped)

    @staticmethod
    def compare_offers(result: AggregatedResult, criteria: CompareCriteria) -> List[ComparedOffer]:
        offers = result.offers
        if not offers:
            return []

        # 计算分数
        prices = [o.price for o in offers if o.price is not None]
        reviews = [o.reviews_count for o in offers if o.reviews_count is not None]

        min_price = min(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0
        min_reviews = min(reviews) if reviews else 0
        max_reviews = max(reviews) if reviews else 0

        compared: List[ComparedOffer] = []
        for o in offers:
            price_component = 0.0
            if criteria.by_price and o.price is not None:
                # 价格越低越好 -> 使用 1 - 归一化价
                norm_p = normalize_score(o.price, min_price, max_price)
                price_component = (1.0 - norm_p) * criteria.price_weight

            reviews_component = 0.0
            if criteria.by_reviews and o.reviews_count is not None:
                norm_r = normalize_score(float(o.reviews_count), float(min_reviews), float(max_reviews))
                reviews_component = norm_r * criteria.reviews_weight

            score = price_component + reviews_component
            compared.append(ComparedOffer(offer=o, score=score))

        compared.sort(key=lambda x: x.score, reverse=True)
        return compared
