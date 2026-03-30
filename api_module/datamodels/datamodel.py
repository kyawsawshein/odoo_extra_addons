from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from typing import List, Optional


class Method:
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


def default_ids(x):
    """Return Odoo default one2many command tuple."""
    return (0, 0, x.__dict__)


@dataclass
class TeableProduct:
    name: str
    location_dest_id: int
    product_id: int
    product_uom: int
    product_uom_qty: Optional[float] = 0.0
    price_unit: Optional[float] = 0.0
    picking_type_id: Optional[int] = None
    picking_id: Optional[int] = None
    move_line_ids: Optional[List] = None
    state: str = "confirmed"
    uom_conversion_id: Optional[int] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}
