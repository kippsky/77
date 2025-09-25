from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.models import ProductQuery, ProductOffer


class SearchProvider(ABC):
    platform: str

    @abstractmethod
    async def search(self, query: ProductQuery) -> List[ProductOffer]:
        raise NotImplementedError
