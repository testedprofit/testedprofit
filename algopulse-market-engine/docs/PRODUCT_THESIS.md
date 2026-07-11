# AlgoPulse Product Thesis

AlgoPulse is not "an arb bot" as the product. AlgoPulse is a market engine.

Use public repos as references, especially Arbitron-style projects and simple educational scanners, but do not build the company by cloning an execution bot. Borrow ideas, compare patterns, and learn what other scanners track. Then rebuild the system inside AlgoPulse's own controlled architecture using official Tinyman, Pact, and Algorand SDKs.

## Correct Product

AlgoPulse Market Engine should become:

- market intelligence
- scanner
- route engine
- paper trading
- risk engine
- execution controls
- public dashboard
- PNET access layer

## Reference Policy

Public repos can help with:

- scanner shape
- route-search ideas
- quote comparison patterns
- dashboard inspiration
- test fixtures and edge cases

Public repos must not provide:

- signer custody
- wallet key handling
- production execution policy
- asset allowlists
- app ID trust
- daily loss policy
- kill-switch policy

## Phase 0 Product Signal

The useful Phase 0 output is not "the bot traded." The useful output is evidence:

- working read-only scanner
- historical quote records
- paper-trade decay and skip reasons
- risk decisions that reject bad routes
- execution controls that keep live funds locked until gates pass
- public receipts for what happened
- delayed dashboard that creates trust without leaking fresh executable routes

That is the foundation for Phase 1: a daily-use Algorand market intelligence product, not a black-box trading script.
