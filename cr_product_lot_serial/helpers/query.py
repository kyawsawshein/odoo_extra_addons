class Query:
    get_lot_expiration = """
        SELECT  sl.id AS location_id
        ,       pp.id AS product_id
        ,       pt.uom_id
        ,       sq.quantity
        ,       st.id As lot_id
        ,       st.avg_cost
        ,       sq.company_id
        FROM stock_quant sq
            INNER JOIN product_product pp ON pp.id=sq.product_id
            INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id
            INNER JOIN stock_location sl ON sl.id=sq.location_id
            INNER JOIN stock_lot st ON st.id=sq.lot_id
        WHERE sq.company_id = {company_id} AND sl.usage IN {location_type}
        AND st.avg_cost <= 0
        AND pt.lot_valuated = {lot_valuated}
        AND st.expiration_date < '{expiration_date}'
    """

class ExpCols:
    LOCATION = 0
    PRODUCT_ID = 1
    UOM_ID = 2
    QUANTITY = 3
    LOT_ID = 4
    AVG_COST = 5
    COMPANY_ID = 6
