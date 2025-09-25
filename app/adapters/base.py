from __future__ import annotations

import abc
from typing import List

from app.models import Offer


class MarketplaceAdapter(abc.ABC):
    """Abstract marketplace adapter that returns a list of offers for a query."""

    @property
    @abc.abstractmethod
    def platform(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def search(self, product_name: str, product_info: str = "") -> List[Offer]:
        raise NotImplementedError

    @property
    def supports_live(self) -> bool:
        """Whether this adapter fetches live data instead of demo data."""
        return False

