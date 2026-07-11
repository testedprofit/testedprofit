"""Gate 3 — local/TestNet x402 smoke (safe checks + guided paid step).

What this script DOES (safe, no secrets, no signing):
  1. Validates TestNet env readiness via the fail-closed loader (names/reasons only).
  2. Hits a running server and asserts the negative paths return 402:
       - unpaid request
       - fake X-PAYMENT header
       - fake PAYMENT-SIGNATURE header
  3. Emits a redacted JSON evidence summary (status codes only).

What this script does NOT do (by design):
  - It never signs, submits, or constructs a payment. The real paid retry must be
    performed by the operator with the official x402 client tooling and a funded
    TestNet payer wallet, per docs/X402_GOPLAUSIBLE_TESTNET_POC_PLAN.md. Signing is
    kept OUTSIDE the market engine. No mnemonic, private key, or full payment
    payload is read, printed, logged, or stored here.

Usage:
  # start the server with TestNet x402 enabled in your local .env, then:
  python scripts/x402_gate3_smoke.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

# Reuse the same fail-closed loader the server uses (no values are printed).
sys.path.insert(0, "src")
from algopulse import x402_testnet  # noqa: E402

ROUTE = "/api/x402/reports/market-pulse/daily"


def _status(url: str, headers: dict | None = None) -> int:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - operator-supplied local URL
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except urllib.error.URLError as exc:  # server not running / unreachable
        print(f"error: could not reach {url}: {exc.reason}", file=sys.stderr)
        return -1


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate 3 x402 safe smoke (no signing, no secrets).")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    # 1) Env readiness (fail closed). Prints only names/reasons, never values.
    config = x402_testnet.load_testnet_config()
    env_ready = config is not None
    print(f"env readiness: {'READY' if env_ready else 'NOT-READY (mock/fail-closed)'}")

    # 2) Negative HTTP checks against a running server.
    url = args.base_url.rstrip("/") + ROUTE
    unpaid = _status(url)
    fake_payment = _status(url, {"X-PAYMENT": "not-a-real-payment"})
    fake_signature = _status(url, {"PAYMENT-SIGNATURE": "not-a-real-signature"})

    checks = {
        "unpaid_returns_402": unpaid == 402,
        "fake_x_payment_stays_402": fake_payment == 402,
        "fake_payment_signature_stays_402": fake_signature == 402,
    }

    evidence = {
        "envReady": env_ready,
        "baseUrl": args.base_url,
        "statusCodes": {
            "unpaid": unpaid,
            "fakeXPayment": fake_payment,
            "fakePaymentSignature": fake_signature,
        },
        "checks": checks,
        # Reminders for the operator-run paid step (kept outside this script):
        "paidStep": "operator-run via official x402 client tooling; never logged here",
        "secretsPrinted": False,
        "paymentPayloadLogged": False,
        "signingPerformedByThisScript": False,
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))

    reachable = unpaid != -1
    return 0 if (reachable and all(checks.values())) else 1


if __name__ == "__main__":
    raise SystemExit(main())
