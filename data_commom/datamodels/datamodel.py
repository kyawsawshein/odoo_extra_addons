from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class ProductValue:
    product_id: int
    value: float
    date: str
    description: str
    lot_id: Optional[int] = None
    move_id: Optional[int] = None
    company_id: Optional[int] = None


@dataclass
class LineData:
    product_id: int
    product_uom_id: int
    location_id: int
    location_dest_id: int
    quantity: float
    lot_id: Optional[int] = None
    lot_name: Optional[str] = None
    move_id: Optional[int] = None


@dataclass
class MoveData:
    location_id: int
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


@dataclass
class PickingData:
    picking_type_id: int
    date_done: date
    location_id: int
    location_dest_id: Optional[int] = None
    move_ids: Optional[List] = None
