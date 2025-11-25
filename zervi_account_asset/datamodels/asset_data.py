from dataclasses import dataclass


@dataclass
class Assets:
    name: str
    code: str
    product_id: int
    quantity: float
    category_id: int
    value: float
    partner_id: int
    company_id: int
    date: str
    date_first_depreciation: str
    method_end: str
    method_time: str
