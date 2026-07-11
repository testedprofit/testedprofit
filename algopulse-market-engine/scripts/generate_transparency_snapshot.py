from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


def _fetch_json(base_url: str) -> dict:
    url = f"{base_url.rstrip('/')}/api/transparency/github-snapshot"
    with urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("ok"):
        raise SystemExit(f"transparency snapshot endpoint failed: {payload.get('error')}")
    return payload["data"]


def _render_markdown(snapshot: dict) -> str:
    proof = snapshot.get("proofSummary") or {}
    ledger = snapshot.get("ledgerSummary") or {}
    audit = snapshot.get("auditSummary") or {}
    commands = snapshot.get("validationCommands") or []
    docs = snapshot.get("docs") or []
    lines = [
        "# AlgoPulse Transparency Snapshot",
        "",
        f"- Generated: `{snapshot.get('generatedAt') or 'unknown'}`",
        f"- Scope: {snapshot.get('scope') or 'public-safe GitHub dossier snapshot'}",
        f"- Proof checks: {proof.get('checks', 0)}",
        f"- Active/complete proof checks: {proof.get('activeOrComplete', 0)}",
        f"- Blocked/limited proof checks: {proof.get('blockedOrLimited', 0)}",
        f"- Payment verification rows: {ledger.get('paymentVerificationCount', 0)}",
        f"- Review event rows: {ledger.get('reviewEventCount', 0)}",
        f"- Checklist items: {audit.get('checklistItems', 0)}",
        f"- Threats tracked: {audit.get('threatsTracked', 0)}",
        "",
        "## Safety",
        "",
        "- Public-safe redacted evidence only.",
        "- No secrets, mnemonics, private keys, payment headers, full payment payloads, or `.env` contents.",
        "- No Mainnet, deployment, signing, live trading, or public eligibility claim is implied.",
        "",
        "## Validation Commands",
        "",
        *[f"- `{command}`" for command in commands],
        "",
        "## Source Docs",
        "",
        *[f"- `{doc}`" for doc in docs],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a redacted AlgoPulse transparency snapshot.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Local API base URL.")
    parser.add_argument("--output", help="Optional markdown output path. Defaults to stdout.")
    args = parser.parse_args()

    markdown = _render_markdown(_fetch_json(args.base_url))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
