from __future__ import annotations

import hashlib
import random
from typing import List

from app.adapters.base import MarketplaceAdapter
from app.models import Offer


class XiaohongshuAdapter(MarketplaceAdapter):
    @property
    def platform(self) -> str:
        return "Xiaohongshu"

    def search(self, product_name: str, product_info: str = "") -> List[Offer]:
        seed = int(hashlib.md5(f"xhs|{product_name}|{product_info}".encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        offers: List[Offer] = []
        for i in range(5):
            price = round(rng.uniform(25, 1800), 2)
            rating = round(rng.uniform(3.9, 5.0), 2)
            reviews = int(rng.uniform(30, 30000))
            shop = f"小红书优选店{i+1}"
            title = f"{product_name} {product_info} 网红推荐 {i+1}"
            url = f"https://www.xiaohongshu.com/explore/{seed + i}"
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

