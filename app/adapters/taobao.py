from __future__ import annotations

import hashlib
import random
from typing import List

from app.adapters.base import MarketplaceAdapter
from app.models import Offer


class TaobaoAdapter(MarketplaceAdapter):
    @property
    def platform(self) -> str:
        return "Taobao"

    def search(self, product_name: str, product_info: str = "") -> List[Offer]:
        # Demo data generator seeded by query for deterministic results
        seed = int(hashlib.md5(f"taobao|{product_name}|{product_info}".encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        offers: List[Offer] = []
        for i in range(5):
            price = round(rng.uniform(20, 2000), 2)
            rating = round(rng.uniform(3.5, 5.0), 2)
            reviews = int(rng.uniform(50, 50000))
            shop = f"TB旗舰店{i+1}"
            title = f"{product_name} {product_info} 高性价比款 {i+1}"
            url = f"https://item.taobao.com/item.htm?id={seed + i}"
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

