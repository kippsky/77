from __future__ import annotations

import hashlib
import random
from typing import List

from app.adapters.base import MarketplaceAdapter
from app.models import Offer


class DouyinAdapter(MarketplaceAdapter):
    @property
    def platform(self) -> str:
        return "Douyin"

    def search(self, product_name: str, product_info: str = "") -> List[Offer]:
        seed = int(hashlib.md5(f"dy|{product_name}|{product_info}".encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        offers: List[Offer] = []
        for i in range(5):
            price = round(rng.uniform(18, 1600), 2)
            rating = round(rng.uniform(3.6, 5.0), 2)
            reviews = int(rng.uniform(20, 60000))
            shop = f"抖音小店{i+1}"
            title = f"{product_name} {product_info} 热卖爆款 {i+1}"
            url = f"https://www.douyin.com/goods/{seed + i}"
            offers.append(
                Offer(
                    platform=self.platform,
                    shop_name=shop,
                    product_title=title,
                    price=price,
                    rating=rating,
                    review_count=reviews,
                    url=url,
                    product_id=str(seed + i),
                )
            )
        return offers

