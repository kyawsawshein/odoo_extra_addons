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

    @classmethod
    def get_list(cls):
        return [(item.code, item.description) for item in cls]


class State(EnumBase):
    DRAFT = ("draft", "Draft")
    OPEN = ("open", "Running")
    CLOSE = ("close", "Close")


class MethodTime(EnumBase):
    NUMBER = ("number", "Number of Entries")
    END = ("end", "Ending Date")


class AssetStart(EnumBase):
    LAST_DAY = ("last_day_period", "Based on Last Day of Purchase Period")
    MANUAL = ("manual", "Manual (Defaulted on Purchase Date)")


class LineStatus(EnumBase):
    DRAFT = ("draft", "Draft")
    PROGRESS = ("progress", "Progress")
    DONE = ("done", "Done")


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
    lot_name: Optional[str] = None
    date_first_depreciation: Optional[str] = None
    method_time: Optional[str] = None
    code: Optional[str] = None
    method_end: Optional[str] = None
    method: Optional[str] = None
    method_number: Optional[int] = 5
    method_period: Optional[int] = 1
    method_progress_factor: Optional[float] = 0.3
    prorata: Optional[bool] = False
    account_analytic_id: Optional[int] = None
    analytic_distribution: Optional[int] = None
