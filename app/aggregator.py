from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List

from app.adapters.base import MarketplaceAdapter
from app.models import Offer


class OfferAggregator:
    def __init__(self, adapters: Iterable[MarketplaceAdapter]) -> None:
        self._adapters = list(adapters)

    def fetch_all(self, product_name: str, product_info: str = "", max_workers: int = 8) -> List[Offer]:
        offers: List[Offer] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(adapter.search, product_name, product_info): adapter
                for adapter in self._adapters
            }
            for future in as_completed(futures):
                adapter = futures[future]
                try:
                    adapter_offers = future.result()
                    offers.extend(adapter_offers)
                except Exception as exc:  # noqa: BLE001
                    # Swallow adapter-specific errors to keep the app resilient
                    offers.append(
                        Offer(
                            platform=adapter.platform,
                            shop_name="(error)",
                            product_title=f"Failed to fetch: {type(exc).__name__}",
                            price=0.0,
                            rating=0.0,
                            review_count=0,
                            url="",
                        )
                    )

        # Sort by price ascending as a default ordering
        offers.sort(key=lambda o: (o.price if o.price > 0 else float("inf")))
        return offers

