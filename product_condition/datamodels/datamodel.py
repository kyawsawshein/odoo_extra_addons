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


class ProductGrade(EnumBase):
    GA = ("ga", "Grade A")
    GB = ("gb", "Grade B")
    GC = ("gc", "Grade C")
