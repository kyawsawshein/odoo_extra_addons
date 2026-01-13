class Query:
    updaate_depreciation = """
        UPDATE account_asset_depreciation_line SET status=%s WHERE id IN %s;
    """

    get_depreciations = """
        SELECT  aaa.product_id
        ,       pc.property_cost_method->>'{company_id}'
        ,       pt.company_id
        ,       aaa.code
        ,       aac.id AS category_id
        ,       st.id AS lot_id
        ,       sm.id AS move_id
        ,       aadl.id
        ,       aadl.depreciation_date
        ,       aaa.value - aadl.amount as amount
        ,		aadl.remaining_value AS value
        FROM account_asset_depreciation_line aadl
            INNER JOIN account_asset_asset aaa ON aaa.id=aadl.asset_id
            INNER JOIN account_asset_category aac ON aac.id=aaa.category_id
            LEFT JOIN product_product pp ON pp.id=aaa.product_id
            LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id
            LEFT JOIN product_category pc ON pc.id=pt.categ_id
            LEFT JOIN stock_picking sp ON sp.name=aaa.code
            LEFT JOIN stock_move_line sml ON sml.picking_id=sp.id
            LEFT JOIN stock_move sm ON sm.id=sml.move_id
            LEFT JOIN stock_lot st ON st.id=sml.lot_id
        WHERE aaa.state='open' AND move_check=false
        ANd aac.group_entries = {group_entries}
        AND aadl.status = '{status}'
        AND aadl.depreciation_date <= '{depreciation_date}'
    """


class DepreCols:
    PRODUCT = 0
    COST_METHOD = 1
    COMPANY_ID = 2
    CODE = 3
    CATEGORY_ID = 4
    LOT_ID = 5
    MOVE_ID = 6
    DEP_IDS = 7
    MONTH = 8
    AMOUNT = 9
    VALUE = 10
