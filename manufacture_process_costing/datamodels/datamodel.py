from enum import Enum
from dataclasses import dataclass
from typing import Optional


def default_ids(x):
    """Return Odoo default one2many command tuple."""
    return (0, 0, x.__dict__)


class EnumBase(Enum):

    @property
    def code(self):
        return self.value[0]

    @property
    def description(self):
        return self.value[1]

    def to_dict(self):
        return {"code": self.code, "description": self.description}

    @classmethod
    def get_list(cls):
        return [(item.code, item.description) for item in cls]

    @classmethod
    def as_dict(cls):
        return {item.code: item.description for item in cls}


class CostMethod(EnumBase):
    MANUAL = ("manually", "Manually")
    WORK_CENTER = ("work-center", "Work Center")


@dataclass
class MaterialCostData:
    material_cost_id: int
    product_id: int
    planned_qty: float
    uom_id: int
    cost_unit: Optional[float] = 0.0
    production_material_id: Optional[int] = None


@dataclass
class LabourCostData:
    labour_cost_id: int
    operation: str
    work_center_id: int
    planned_minute: float
    cost_minute: Optional[float] = 0.0
    production_labour_id: Optional[int] = None


@dataclass
class OverheadCostData:
    overhead_cost_id: int
    operation: str
    work_center_id: int
    planned_minute: float
    cost_minute: Optional[float] = 0.0
    production_overhead_id: Optional[int] = None
