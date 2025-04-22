from tradingview_screener import Query, col

def preset_52_week_high():
    return (
        Query()
        .where(
            col('is_primary') == True,
            col('typespecs').has('common'),
            col('type') == 'stock',
            col('price_52_week_high') <= 'high',
            col('active_symbol') == True,
        )
        .order_by('name', ascending=True, nulls_first=False)
        .limit(100)
        .set_markets('india')
        .set_property('symbols', {'query': {'types': ['stock', 'fund', 'dr']}})
        .set_property('preset', 'above_52wk_high')
    )

def preset_biggest_losers():
    return (
        Query()
        .where(
            col('is_primary') == True,
            col('typespecs').has('common'),
            col('type') == 'stock',
            col('change') < 0,
            col('active_symbol') == True,
        )
        .order_by('change', ascending=True, nulls_first=False)
        .limit(100)
        .set_markets('india')
        .set_property('symbols', {'query': {'types': ['stock', 'fund', 'dr']}})
        .set_property('preset', 'losers')
    )

PRESET_QUERIES = {
    "52-week high": preset_52_week_high,
    "Biggest losers": preset_biggest_losers,
    # Add more mappings as needed
}
