from algopulse.demo import run_five_to_ten_demo


def test_five_to_ten_demo_is_synthetic_and_doubles_algo():
    demo = run_five_to_ten_demo()

    assert demo["mode"] == "synthetic-demo"
    assert demo["live"] is False
    assert demo["input_amount"] == 5.0
    assert demo["output_amount"] == 10.0
    assert demo["net_profit_algo"] > 4.9
    assert "Synthetic proof run" in demo["warning"]

