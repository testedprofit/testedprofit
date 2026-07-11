# Risk Policy

## Starting Rule

The risk engine should reject most opportunities. A route is interesting only when it clears profit, freshness, impact, route length, allowlist, fee-buffer, daily-cap, and concurrency gates.

## Pure Risk Inputs

`RiskEvaluationInput` captures deterministic inputs:

- trade size and trade-size limit
- net expected profit and profit bps
- total expected fees and fee-buffer multiplier
- quote age and max quote age
- route length and max route length
- asset and app allowlist results
- pool reserve result
- daily loss and daily trade counters
- concurrent execution count

`evaluate_risk_rules` returns the first failed rule plus the full rule map. It has no network, store, or clock dependency.

## Initial Limits

- max trade size: 10 ALGO in Phase 0
- max daily loss: 20 ALGO
- max daily trades: 20
- max route length: 3 swaps
- max concurrent execution: 1
- quote age: 5 seconds or less
- minimum profit: greater than 0.25 start units and 35 bps
- price impact: 50 bps default ceiling
- fee buffer: at least 2x expected total fees

Live execution remains out of scope for this control-plane pass.
