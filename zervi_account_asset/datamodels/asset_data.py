from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EnumBase(Enum):

    @property
    def code(self):
        """Returns the code part of the value tuple."""
        return self.value[0]

    @property
    def description(self):
        """Returns the description part of the value tuple."""
        return self.value[1]


class MethodTime(EnumBase):
    NUMBER = ("number", "Number of Entries")
    END = ("end", "Ending Date")


class AssetStart(EnumBase):
    LAST_DAY = ("last_day_period", "Based on Last Day of Purchase Period")
    MANUAL = ("manual", "Manual (Defaulted on Purchase Date)")


@dataclass
class Assets:
    name: str
    product_id: int
    quantity: float
    category_id: int
    value: float
    partner_id: int
    company_id: int
    date: str
    date_first_depreciation: Optional[str] = None
    method_time: Optional[str] = None
    code: Optional[str] = None
    method_end: Optional[str] = None
