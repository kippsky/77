from __future__ import annotations

import hashlib
import random
from typing import List

from app.adapters.base import MarketplaceAdapter
from app.models import Offer


class JDAdapter(MarketplaceAdapter):
    @property
    def platform(self) -> str:
        return "JD"

    def search(self, product_name: str, product_info: str = "") -> List[Offer]:
        seed = int(hashlib.md5(f"jd|{product_name}|{product_info}".encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        offers: List[Offer] = []
        for i in range(5):
            price = round(rng.uniform(30, 2200), 2)
            rating = round(rng.uniform(3.8, 5.0), 2)
            reviews = int(rng.uniform(80, 80000))
            shop = f"京东自营{i+1}"
            title = f"{product_name} {product_info} 官方正品 {i+1}"
            url = f"https://item.jd.com/{seed + i}.html"
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

