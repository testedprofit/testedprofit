from __future__ import annotations

import time


def run_five_to_ten_demo() -> dict:
    input_algo = 5.0
    output_algo = 10.0
    estimated_group_fee = 0.004
    net_profit = output_algo - input_algo - estimated_group_fee

    return {
        "mode": "synthetic-demo",
        "live": False,
        "submitted": False,
        "input_asset": "ALGO",
        "input_amount": input_algo,
        "output_asset": "ALGO",
        "output_amount": output_algo,
        "estimated_group_fee_algo": estimated_group_fee,
        "net_profit_algo": net_profit,
        "net_profit_bps": (net_profit / input_algo) * 10_000,
        "route": [
            {
                "venue": "demo-pact",
                "pair": "ALGO/DEMO-USDC",
                "input": "5.0000 ALGO",
                "output": "1.0000 DEMO-USDC",
            },
            {
                "venue": "demo-tinyman",
                "pair": "DEMO-USDC/ALGO",
                "input": "1.0000 DEMO-USDC",
                "output": "10.0000 ALGO",
            },
        ],
        "checks": {
            "route_leg_count_ok": True,
            "max_trade_size_ok": True,
            "asset_allowlist_ok": True,
            "group_size_ok": True,
            "fee_ceiling_ok": True,
            "dry_run_only": True,
        },
        "warning": "Synthetic proof run only. This is not live market profit and uses no funds.",
        "created_at": time.time(),
    }

