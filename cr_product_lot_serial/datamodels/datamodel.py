from ...data_commom.datamodels.enum_data import EnumBase


class LocationType(EnumBase):
    SUPPLIER = ("supplier", "Vendor")
    VIEW = ("view", "Virtual")
    INTERNAL = ("internal", "Internal")
    CUSTOMER = ("customer", "Customer")
    INVENTORY = ("inventory", "Inventory Loss")
    PRODUCTION = ("production", "Production")
    TRANSIT = ("transit", "Transit")
