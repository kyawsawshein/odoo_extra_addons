from enum import Enum

class EnumBase(Enum):

    @property
    def code(self):
        return self.value[0]

    @property
    def description(self):
        return self.value[1]

    def to_dict(self):
        return {
            "code": self.code,
            "description": self.description
        }

    @classmethod
    def get_list(cls):
        return [(item.code, item.description) for item in cls]

    @classmethod
    def as_dict(cls):
        return {item.code: item.description for item in cls}


class CostMethod(EnumBase):
    MANUAL = ("manually", "Manually")
    WORK_CENTER = ("work-center", "Work Center")
