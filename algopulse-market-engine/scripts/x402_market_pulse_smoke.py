from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any


ENDPOINT = "/api/x402/reports/market-pulse/daily"
MOCK_PROOF_HEADER = "X-Algopulse-Mock-X402-Proof"
MOCK_PROOF_VALUE = "mock_x402_report_access"
RAW_ROUTE_KEYS = {
    "route",
    "routehash",
    "route_hash",
    "routejson",
    "route_json",
    "legs",
    "inputassetid",
    "input_asset_id",
    "outputassetid",
    "output_asset_id",
    "expectedoutput",
    "expected_output",
    "involvedpoolids",
    "involved_pool_ids",
    "involvedassetids",
    "involved_asset_ids",
}
UNSAFE_VALUE_FRAGMENTS = (
    "signed_transaction",
    "signedtransaction",
    "signed_txn",
    "signedtxn",
    "signed_group",
    "submission_payload",
    "submitted_txid",
    "submitted_transaction",
    "hot_wallet",
    "hot wallet",
    "private_key",
    "privatekey",
    "mnemonic",
    "seed_phrase",
    "seed phrase",
    "wallet_mnemonic",
    "unsigned_group",
    "unsignedtxngroup",
)


class SmokeFailure(RuntimeError):
    pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test the mock/TestNet x402 market-pulse paid report endpoint."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8765",
        help="Running AlgoPulse API base URL. Default: http://127.0.0.1:8765",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds.")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    try:
        unpaid = _request_json(f"{base_url}{ENDPOINT}", timeout=args.timeout)
        _assert_unpaid(unpaid)
        paid = _request_json(
            f"{base_url}{ENDPOINT}",
            timeout=args.timeout,
            headers={MOCK_PROOF_HEADER: MOCK_PROOF_VALUE},
        )
        _assert_paid(paid)
    except SmokeFailure as exc:
        print(f"x402 market-pulse smoke failed: {exc}", file=sys.stderr)
        return 1

    print("x402 market-pulse smoke passed")
    print(f"- baseUrl: {base_url}")
    print("- unpaid request: HTTP 402")
    print("- mock paid request: HTTP 200")
    print("- paid response: redacted delayed report, no unsafe route/signer/execution artifacts found")
    return 0


def _request_json(url: str, *, timeout: float, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {
                "status": response.status,
                "headers": {key.lower(): value for key, value in response.headers.items()},
                "body": _json_body(response.read(), url),
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "headers": {key.lower(): value for key, value in exc.headers.items()},
            "body": _json_body(exc.read(), url),
        }
    except urllib.error.URLError as exc:
        raise SmokeFailure(f"could not reach {url}: {exc}") from exc
    except TimeoutError as exc:
        raise SmokeFailure(f"request timed out for {url}: {exc}") from exc


def _json_body(raw: bytes, url: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise SmokeFailure(f"{url} did not return JSON") from exc
    if not isinstance(payload, dict):
        raise SmokeFailure(f"{url} returned non-object JSON")
    return payload


def _assert_unpaid(response: dict[str, Any]) -> None:
    if response["status"] != 402:
        raise SmokeFailure(f"unpaid request returned HTTP {response['status']}, expected 402")
    header = response["headers"].get("x-algopulse-payment-required")
    if header != "mock-x402-readiness":
        raise SmokeFailure("unpaid response missing x-algopulse-payment-required=mock-x402-readiness")
    body = response["body"]
    error = body.get("error") or {}
    details = error.get("details") or {}
    if error.get("code") != "X402_PAYMENT_REQUIRED":
        raise SmokeFailure("unpaid response error.code is not X402_PAYMENT_REQUIRED")
    if details.get("mode") != "mock-testnet-readiness":
        raise SmokeFailure("unpaid response is not labeled mock-testnet-readiness")
    if details.get("acceptedProofHeader") != MOCK_PROOF_HEADER:
        raise SmokeFailure("unpaid response does not document the mock proof header")
    if details.get("acceptedProofValue") != MOCK_PROOF_VALUE:
        raise SmokeFailure("unpaid response does not document the mock proof value")


def _assert_paid(response: dict[str, Any]) -> None:
    if response["status"] != 200:
        raise SmokeFailure(f"mock paid request returned HTTP {response['status']}, expected 200")
    body = response["body"]
    if body.get("ok") is not True:
        raise SmokeFailure("mock paid response ok is not true")
    data = body.get("data") or {}
    report = data.get("report") or {}
    if data.get("mode") != "mock-testnet-readiness":
        raise SmokeFailure("mock paid response is not labeled mock-testnet-readiness")
    if data.get("proofAccepted") is not True:
        raise SmokeFailure("mock paid response did not accept the proof")
    if data.get("liveExecutionTouched") is not False or data.get("signerCodeTouched") is not False:
        raise SmokeFailure("mock paid wrapper does not preserve live/signer safety flags")
    if report.get("publicSafe") is not True:
        raise SmokeFailure("report is not marked publicSafe=true")
    if report.get("liveExecutionTouched") is not False or report.get("signerCodeTouched") is not False:
        raise SmokeFailure("report does not preserve live/signer safety flags")
    _assert_no_unsafe_payload(body)


def _assert_no_unsafe_payload(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for fragment in UNSAFE_VALUE_FRAGMENTS:
        if fragment in serialized:
            raise SmokeFailure(f"paid response contains unsafe fragment: {fragment}")
    for path, _value in _walk_json(payload):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        normalized = key.replace("-", "_").lower()
        if normalized in RAW_ROUTE_KEYS:
            raise SmokeFailure(f"paid response contains raw route field: {path}")


def _walk_json(value: object, path: str = "$") -> Iterator[tuple[str, object]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, f"{path}[{index}]")


if __name__ == "__main__":
    raise SystemExit(main())
