from algopulse.models import Pool


def test_pool_quote_uses_constant_product_math():
    pool = Pool(
        pool_id="test",
        venue_id="venue",
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=1000.0,
        reserve_b=200.0,
        fee_bps=30,
        block_round=1,
    )

    quote = pool.quote(input_asset_id=0, input_amount=10.0)

    assert quote is not None
    assert quote.output_asset_id == 31566704
    assert 1.9 < quote.output_amount < 2.0
    assert quote.price_impact_bps > 0

