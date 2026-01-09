class Query:
    updaate_depreciation = """
        UPDATE account_asset_depreciation_line SET status=%s WHERE id IN %s;
        """
