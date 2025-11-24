from pydantic import BaseModel


class ProductValue(BaseModel):
    product_id: int
    value: float
    company_id: int
    date: str
    description: str
