# Initial PNET Test Pools

These are the initial Phase 0 arbitrage testing pairs from the Vestige PNET pool list screenshot.

Target asset: PNET / ProfitNet, ASA `3169177585`.

| Rank | Pair | Other ASA | Vestige ticker | Target reserve | Protocol IDs |
| --- | --- | ---: | --- | ---: | --- |
| 1 | PNET / XDB | `1290751153` | XDB | 2836274.001520 | `3` |
| 2 | PNET / BSF | `3436365167` | BSF | 1969721.940610 | `3` |
| 3 | PNET / ELGSQ | `1893942045` | ELGSQ | 1733398.483125 | `3` |
| 4 | PNET / USDC | `31566704` | USDC | 1514348.842533 | `3` |
| 5 | PNET / Max | `1390638935` | Max | 1449673.493649 | `3` |
| 6 | PNET / FUCKAI | `2644742542` | FUCKAI | 881221.705544 | `3` |
| 7 | PNET / BSB | `3249403496` | BSB | 811465.855860 | `3` |
| 8 | PNET / crashout | `3427156477` | crashout | 809524.296667 | `3` |
| 9 | PNET / THC | `1119722936` | THC | 1137433.066962 | `2,3` |
| 10 | PNET / BLOBOB | `3410350791` | BLOBOB | 400222.867324 | `3` |
| 11 | PNET / DERS | `846652486` | DERS | 460716.868358 | `3` |
| 12 | PNET / AURA | `3427041827` | AURA | 359022.550881 | `3` |
| 13 | PNET / AETF | `1674484158` | AETF | 373515.917307 | `2,3` |
| 14 | PNET / Pawbucks | `3227174563` | Pawbucks | 156130.711390 | `3` |

Protocol IDs follow the current Vestige mapping used by the app:

- `2` = Tinyman v2
- `3` = Pact

Use this env var to pin discovery to this list:

```bash
ALGO_PULSE_VESTIGE_PINNED_PAIR_ASSET_IDS=1290751153,3436365167,1893942045,31566704,1390638935,2644742542,3249403496,3427156477,1119722936,3410350791,846652486,3427041827,1674484158,3227174563
ALGO_PULSE_VESTIGE_INCLUDE_FALLBACK_PAIRS=false
```

This pinned mode is for scanner/paper-trade testing first. Most of these routes start and end in PNET or the paired ASA, while the current live executor is intentionally ALGO-starting only until non-ALGO profit denomination and wallet inventory checks are reviewed.
