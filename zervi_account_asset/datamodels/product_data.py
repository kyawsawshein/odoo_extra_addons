from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductValue:
    product_id: int
    value: float
    date: str
    description: str
    lot_id: Optional[int] = None
    move_id: Optional[int] = None
    company_id: Optional[int] = None
