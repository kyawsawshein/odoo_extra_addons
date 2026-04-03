class StockSQL:
    stock_lot = """
        SELECT lot.id,lot.name,pt.default_code AS product,sq.quantity,lot.standard_price->'1' AS cost, EXTRACT(EPOCH FROM lot.write_date) AS write_date
        FROM stock_lot lot
            INNER JOIN product_product pp ON pp.id=lot.product_id
            INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id
            INNER JOIN stock_quant sq ON sq.lot_id=lot.id
        WHERE sq.quantity > 0
        AND lot.write_date > %s
        ORDER BY lot.write_date
    """


class PartnerSQL:
    partner = """
        SELECT rp.id,rp.name,rp.email,rp.phone,rp.vat AS tax_id,rc.name->'en_US' AS country, EXTRACT(EPOCH FROM rp.write_date) AS write_date
        FROM res_partner rp
            LEFT JOIN res_country rc ON rc.id=rp.country_id
        WHERE rp.write_date > %s
    """


class ProductSQL:
    producdt = """
        SELECT pp.id,pt.default_code,pp.barcode,pc.complete_name,pp.standard_price->'1' AS standard_price,pt.list_price,uom.name->'en_US' AS uom_id, EXTRACT(EPOCH FROM pp.write_date) AS write_date
        FROM product_product pp
            INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id
            INNER JOIN product_category pc ON pc.id=pt.categ_id
            INNER JOIN uom_uom uom ON uom.id=pt.uom_id
        WHERE pp.write_date > %s
        ORDER BY pp.write_date
    """
