from dataclasses import asdict, dataclass, fields
from datetime import date
from enum import Enum
from typing import List, Dict, Optional


class Method:
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


def default_ids(x):
    """Return Odoo default one2many command tuple."""
    return (0, 0, x.__dict__)


@dataclass
class TableJobParams:
    table_id: str
    method: str
    records: List[Dict]

@dataclass
class BaseClass:
    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

    def get_fields(self):
        return [f.name for f in fields(self)]


@dataclass
class TeableProduct(BaseClass):
    id: int
    default_code: str
    name: str
    barcode: str
    categ_id: int
    standard_price: float
    list_price: float
    qty_available: float
    uom_id: int
    write_date: int


@dataclass
class TeablePartner(BaseClass):
    name: str
    email: str
    phone: str
    country_id: int
    vat: str
    write_date: int
    property_payment_term_id: Optional[int] = None
    # property_supplier_payment_term_id: Optional[int] = None


@dataclass
class TeableStockLot(BaseClass):
    name: str
    product_id: int
    product_qty: float
    standard_price: float
    expiration_date: str
    location_id: Optional[int] = None
