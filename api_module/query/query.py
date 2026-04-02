class StockSQL:
    stock_lot = """
        SELECT lot.name,pt.default_code AS product,sq.quantity,lot.standard_price->'1' AS cost, EXTRACT(EPOCH FROM lot.write_date) AS write_date
        FROM stock_lot lot
            INNER JOIN product_product pp ON pp.id=lot.product_id
            INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id
            INNER JOIN stock_quant sq ON sq.lot_id=lot.id
        WHERE sq.quantity > 0
        AND lot.write_date > %s
        ORDER BY lot.write_date
        {}
    """
