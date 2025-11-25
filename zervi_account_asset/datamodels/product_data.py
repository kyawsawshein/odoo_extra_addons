from dataclasses import dataclass


@dataclass
class ProductValue:
    product_id: int
    value: float
    company_id: int
    date: str
    description: str
