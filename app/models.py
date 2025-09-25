from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Offer:
    platform: str
    shop_name: str
    product_title: str
    price: float
    rating: float  # 0.0 - 5.0
    review_count: int
    url: str
    product_id: Optional[str] = None
    currency: str = "CNY"
    extra: Dict[str, str] = field(default_factory=dict)


def compute_score(
    offer: Offer,
    min_price: float,
    max_price: float,
    weight_price: float,
    weight_rating: float,
    weight_reviews: float,
) -> float:
    """Compute a composite score for an offer based on weighted criteria.

    - Price: lower is better, normalized between min and max seen prices
    - Rating: higher is better (0-5)
    - Reviews: higher is better, log-scaled
    """
    # Avoid division by zero in normalization
    price_range = max(max_price - min_price, 1e-6)
    # Normalize price to 0..1 where 1 is best (cheapest)
    normalized_price = 1.0 - (offer.price - min_price) / price_range

    # Normalize rating 0..1 (5 is best)
    normalized_rating = max(min(offer.rating / 5.0, 1.0), 0.0)

    # Normalize reviews using log scale to dampen huge counts
    import math

    normalized_reviews = math.log10(max(offer.review_count, 1)) / 6.0  # 10^6 -> 1.0
    normalized_reviews = max(min(normalized_reviews, 1.0), 0.0)

    total_weight = max(weight_price + weight_rating + weight_reviews, 1e-6)
    score = (
        normalized_price * weight_price
        + normalized_rating * weight_rating
        + normalized_reviews * weight_reviews
    ) / total_weight
    return score

